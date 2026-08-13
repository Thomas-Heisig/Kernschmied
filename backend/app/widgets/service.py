from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import logging
from sqlalchemy import select
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import HierarchyNode, WidgetRegistry, WidgetAssignment
from app.core.settings import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ResolvedWidget:
    item: dict
    source: str
    source_node_id: str | None


class WidgetResolverService:
    """Resolves effective widgets for a hierarchy node using registry + assignments.

    The service is deliberately defensive: widget resolution isolates errors
    per-widget and logs problems instead of failing the entire resolution.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _choose_registry_candidate(self, rows: list[WidgetRegistry] | list, requested_key: str | None = None):
        """Deterministically choose a registry row from possible duplicates.

        Selection order:
        1. row.id == requested_key
        2. row.name == requested_key
        3. row.status == 'active'
        4. first row

        Logs a warning (without raising) when multiple candidates exist.
        """
        if not rows:
            return None
        if requested_key is not None:
            for cand in rows:
                if getattr(cand, "id", None) == requested_key:
                    return cand
            for cand in rows:
                if getattr(cand, "name", None) == requested_key:
                    return cand
        for cand in rows:
            if getattr(cand, "status", None) == "active":
                return cand
        selected = rows[0]
        if len(rows) > 1:
            try:
                ids = [getattr(r, "id", None) for r in rows]
                logger.warning(
                    "widget_registry_duplicate_detected requested_key=%s candidate_ids=%s selected_id=%s",
                    requested_key,
                    ids,
                    getattr(selected, "id", None),
                )
            except Exception:
                logger.warning("widget_registry_duplicate_detected requested_key=%s selected_first_candidate", requested_key)
        return selected

    async def _load_chain(self, node_id: str) -> list[HierarchyNode]:
        chain: list[HierarchyNode] = []
        stmt = select(HierarchyNode).where(HierarchyNode.id == node_id)
        res = await self._session.execute(stmt)
        cur = res.scalar_one_or_none()
        if cur is None:
            return []
        while cur is not None:
            chain.append(cur)
            if not cur.parent_id:
                break
            stmt = select(HierarchyNode).where(HierarchyNode.id == cur.parent_id)
            res = await self._session.execute(stmt)
            cur = res.scalar_one_or_none()

        return list(reversed(chain))

    def _actor_perms(self, actor: Any) -> set[str]:
        if actor is None:
            return set()
        perms = set(getattr(actor, "permissions", ()) or ()) | set(getattr(actor, "roles", ()) or ())
        return {str(p) for p in perms}

    async def resolve_effective_widgets(self, node_id: str, actor: Any) -> list[dict]:
        chain = await self._load_chain(node_id)
        if not chain:
            return []

        has_db = self._session is not None
        # Diagnostic: log bound engine/connection info and existence of widget_assignments rows
        if has_db:
            try:
                # Log configured effective database URL for diagnostics
                try:
                    logger.info("widget_resolver: effective_database_url=%s", settings.effective_database_url)
                except Exception:
                    logger.debug("widget_resolver: could not read effective_database_url", exc_info=True)
                # Attempt to inspect the session bind/engine for debugging
                try:
                    bind = self._session.get_bind()
                except Exception:
                    bind = None
                logger.debug("widget_resolver: session.bind=%r", bind)
                # Try a simple COUNT(*) to confirm visibility of the table
                from sqlalchemy import text

                try:
                    cnt_res = await self._session.execute(text("SELECT COUNT(*) FROM widget_assignments"))
                    try:
                        cnt = cnt_res.scalar_one()
                    except Exception:
                        # fallback to fetching first column
                        cnt = (cnt_res.fetchone() or (0,))[0]
                    logger.info("widget_resolver: widget_assignments row_count=%s", cnt)
                except Exception:
                    logger.exception("widget_resolver: failed to COUNT widget_assignments")

                # Try sampling a few rows for debugging
                try:
                    sample_res = await self._session.execute(text("SELECT id,node_id,widget_id,name FROM widget_assignments LIMIT 5"))
                    rows = sample_res.fetchall()
                    logger.debug("widget_resolver: sample widget_assignments rows=%r", rows)
                except Exception:
                    logger.debug("widget_resolver: failed to fetch sample rows from widget_assignments", exc_info=True)
            except Exception:
                logger.debug("widget_resolver: debug DB inspection failed", exc_info=True)
        

        # Actor permissions/roles mapping
        actor_perms = self._actor_perms(actor)
        # Consider explicit system admin flag as well as roles/permissions
        is_admin = bool(getattr(actor, "is_system_admin", False)) or "admin" in actor_perms or "*" in actor_perms
        # NOTE: do NOT short-circuit resolution when a system-node appears in the chain.
        # Permissions are enforced per-widget/assignment below.

        effective_map: dict[str, ResolvedWidget] = {}
        order: list[ResolvedWidget] = []

        def widget_key(w: dict) -> str:
            # prefer explicit id/widget_id/name
            for k in ("id", "widget_id", "name"):
                v = w.get(k)
                if v:
                    return str(v)
            # fallback to component_type+label
            return f"<{w.get('component_type') or w.get('type')}>:{w.get('label') or ''}"

        for n in chain:
            # First: apply registry-level defaults where registry.name == node.type
            try:
                if has_db:
                    stmt = select(WidgetRegistry).where(WidgetRegistry.name == n.type)
                    res = await self._session.execute(stmt)
                    rows = res.scalars().all()
                    reg = self._choose_registry_candidate(rows, n.type)
                else:
                    reg = None
                if reg is not None and getattr(reg, "status", "active") != "deprecated":
                    defaults = getattr(reg, "default_config", {}) or {}
                    defaults_list = defaults.get("default_widgets") if isinstance(defaults, dict) else None
                    if isinstance(defaults_list, list):
                        for w in defaults_list:
                            try:
                                key = widget_key(w)
                                if key in effective_map:
                                    continue
                                # permission check
                                required = getattr(reg, "required_permissions", []) or []
                                if required and not actor_perms.intersection({str(x) for x in required}):
                                    continue
                                effective_map[key] = ResolvedWidget(item=w, source="registry_default", source_node_id=None)
                                order.append(effective_map[key])
                            except Exception:
                                logger.exception("Failed to apply registry default widget for node %s", n.id)
            except Exception:
                logger.exception("Failed to load registry defaults for node type %s", n.type)

            # Then: explicit assignments on the node. Prefer relational table if present.
            try:
                if has_db:
                    stmt = select(WidgetAssignment).where(WidgetAssignment.node_id == n.id)
                    res = await self._session.execute(stmt)
                    assigns_rows = res.scalars().all()
                else:
                    assigns_rows = None
            except Exception:
                assigns_rows = None

            # If ORM returned none/empty, try raw SQL fallback to ensure we
            # discover assignments even when the ORM mapping doesn't match
            # the on-disk schema exactly.
            if not assigns_rows and has_db:
                try:
                    from sqlalchemy import text

                    q = text(
                        "SELECT id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions FROM widget_assignments WHERE node_id = :nid"
                    )
                    res2 = await self._session.execute(q, {"nid": n.id})
                    assigns_rows = res2.fetchall()
                except Exception:
                    assigns_rows = None

            if isinstance(assigns_rows, list):
                try:
                    logger.info("Node %s: loaded %d relational assignments", n.id, len(assigns_rows))
                except Exception:
                    pass

            assigns: list[dict] = []
            if isinstance(assigns_rows, list) and assigns_rows:
                for row in assigns_rows:
                    try:
                        # support both ORM-mapped objects and raw SQL row tuples
                        if hasattr(row, "widget_id") or hasattr(row, "id"):
                            # Prefer the stored widget_id for public item `id`.
                            # Do NOT fall back to the assignment PK here — the
                            # assignment primary key is an internal identifier
                            # and should not be exposed as the widget id.
                            wid = getattr(row, "widget_id", None)
                            assignment_pk = getattr(row, "id", None)
                            name = getattr(row, "name", None)
                            comp_type = None
                            position = getattr(row, "position", None)
                            configuration = getattr(row, "configuration", None)
                            enabled = getattr(row, "enabled", True)
                            inherit = getattr(row, "inherit", True)
                            required_permissions = getattr(row, "required_permissions", None)
                        else:
                            # raw tuple order: id,node_id,widget_id,name,enabled,inherit,position,configuration,required_permissions
                            try:
                                wid = row[2]
                                name = row[3]
                                enabled = bool(row[4])
                                inherit = bool(row[5])
                                position = row[6]
                                configuration = row[7]
                                required_permissions = row[8]
                            except Exception:
                                # best-effort fallback
                                wid = None
                                name = None
                                enabled = True
                                inherit = True
                                position = None
                                configuration = None
                                required_permissions = None

                        assigns.append({
                            # `id` should reflect the declared widget id (widget_id),
                            # not the internal assignment PK. The resolver will
                            # enrich `id`/`name` from the registry when possible.
                            "id": wid or None,
                            "name": name,
                            "component_type": comp_type,
                            "position": position,
                            "configuration": configuration,
                            "enabled": enabled,
                            "inherit": inherit,
                            "required_permissions": required_permissions or [],
                        })
                    except Exception:
                        logger.exception("Failed to map widget assignment row for node %s", n.id)
            else:
                # fallback to legacy JSON assignments on the node
                assigns = getattr(n, "widget_assignments", None) or []

            if isinstance(assigns, list):
                # Log number of assignments for this node and raw content
                try:
                    logger.info("widget_resolver: node=%s assignments_count=%d (source=relational_or_json)", n.id, len(assigns))
                    logger.info("widget_resolver: node=%s raw_assigns=%r", n.id, assigns)
                except Exception:
                    pass

                for w in assigns:
                    if not isinstance(w, dict):
                        continue
                    try:
                        # Basic assignment fields
                        assign_id = w.get("id") or w.get("widget_id") or w.get("name")
                        widget_id = w.get("id")
                        node_id_field = n.id
                        enabled = bool(w.get("enabled", True))
                        inherit = bool(w.get("inherit", True))
                        position = w.get("position")
                        reqs_field = w.get("required_permissions") or w.get("visible_to") or []

                        logger.debug(
                            "widget_resolver: assignment load node=%s assignment_id=%s widget_id=%s enabled=%s inherit=%s position=%s required_permissions=%s",
                            node_id_field,
                            assign_id,
                            widget_id,
                            enabled,
                            inherit,
                            position,
                            list(reqs_field) if isinstance(reqs_field, (list, tuple)) else [],
                        )

                        # Decide inheritance/directness
                        is_direct = (n.id == node_id)

                        # Collect filter reasons
                        skip_reasons: list[str] = []

                        if not is_direct and not inherit:
                            skip_reasons.append("skipped_not_inherited")

                        if not enabled:
                            skip_reasons.append("skipped_disabled")

                        # Permission check
                        if isinstance(reqs_field, (list, tuple)) and reqs_field:
                            if not actor_perms.intersection({str(x) for x in reqs_field}):
                                skip_reasons.append("skipped_permission")

                        # Registry lookup
                        reg_entry = None
                        reg_info = {
                            "found": False,
                            "status": None,
                            "type": None,
                            "component_type": None,
                            "required_permissions": [],
                            "supported_node_types": None,
                        }
                        try:
                            if has_db:
                                from sqlalchemy.exc import MultipleResultsFound

                                stmt = select(WidgetRegistry).where(WidgetRegistry.name == (assign_id or widget_id))
                                res = await self._session.execute(stmt)
                                # Prefer a single match; if multiple results exist, select
                                # the best candidate (id==name, then active status, else first).
                                rows = res.scalars().all()
                                if not rows:
                                    reg_entry = None
                                elif len(rows) == 1:
                                    reg_entry = rows[0]
                                else:
                                    # multiple rows: try to pick canonical id==name
                                    reg_entry = None
                                    for cand in rows:
                                        if getattr(cand, "id", None) == (assign_id or widget_id):
                                            reg_entry = cand
                                            break
                                    if reg_entry is None:
                                        for cand in rows:
                                            if getattr(cand, "status", None) == "active":
                                                reg_entry = cand
                                                break
                                    if reg_entry is None:
                                        reg_entry = rows[0]
                                    logger.warning(
                                        "widget_resolver: multiple registry entries found for name=%s; selected id=%s",
                                        assign_id,
                                        getattr(reg_entry, "id", None),
                                    )
                        except Exception:
                            logger.debug("widget_resolver: registry lookup failed for assignment_id=%s on node=%s", assign_id, n.id)

                        if reg_entry is None:
                            # try lookup by widget_id if different
                            try:
                                if has_db and widget_id and widget_id != assign_id:
                                    stmt = select(WidgetRegistry).where(WidgetRegistry.name == widget_id)
                                    res = await self._session.execute(stmt)
                                    rows = res.scalars().all()
                                    if not rows:
                                        reg_entry = None
                                    elif len(rows) == 1:
                                        reg_entry = rows[0]
                                    else:
                                        reg_entry = None
                                        for cand in rows:
                                            if getattr(cand, "id", None) == widget_id:
                                                reg_entry = cand
                                                break
                                        if reg_entry is None:
                                            for cand in rows:
                                                if getattr(cand, "status", None) == "active":
                                                    reg_entry = cand
                                                    break
                                        if reg_entry is None:
                                            reg_entry = rows[0]
                                        logger.warning(
                                            "widget_resolver: multiple registry entries found for widget_id=%s; selected id=%s",
                                            widget_id,
                                            getattr(reg_entry, "id", None),
                                        )
                            except Exception:
                                pass

                        if reg_entry is not None:
                            reg_info["found"] = True
                            reg_info["status"] = getattr(reg_entry, "status", None)
                            reg_info["type"] = getattr(reg_entry, "type", None)
                            # read metadata from possible fields
                            md = getattr(reg_entry, "widget_metadata", None)
                            if md is None:
                                md = getattr(reg_entry, "metadata", None)
                            if isinstance(md, str):
                                try:
                                    md = json.loads(md)
                                except Exception:
                                    md = {}
                            md = md or {}
                            reg_info["component_type"] = md.get("component_type") or getattr(reg_entry, "type", None)
                            reg_info["required_permissions"] = getattr(reg_entry, "required_permissions", []) or md.get("required_permissions", []) or []
                            reg_info["supported_node_types"] = md.get("supported_node_types")

                        logger.debug(
                            "widget_resolver: registry_lookup node=%s assignment_id=%s registry_found=%s status=%s type=%s component_type=%s supported_node_types=%s required_permissions=%s",
                            n.id,
                            assign_id,
                            bool(reg_info["found"]),
                            reg_info["status"],
                            reg_info["type"],
                            reg_info["component_type"],
                            reg_info["supported_node_types"],
                            reg_info["required_permissions"],
                        )

                        # Filtering decisions based on registry
                        if reg_entry is not None and reg_info.get("status") == "deprecated":
                            skip_reasons.append("skipped_deprecated")

                        supported = reg_info.get("supported_node_types")
                        # Semantics:
                        # - missing or None -> no restriction (allowed everywhere)
                        # - empty list -> no restriction (allowed everywhere)
                        # - list containing '*' -> explicit allow-all
                        # - otherwise treat list as whitelist of allowed node types
                        # Note: direct assignments remain authoritative for that node.
                        if isinstance(supported, list) and supported:
                            try:
                                if "*" in supported:
                                    # explicit allow-all
                                    pass
                                else:
                                    if n.type not in supported and not is_direct:
                                        skip_reasons.append("skipped_unsupported_node_type")
                            except Exception:
                                # if supported is malformed, do not block by default
                                logger.debug("widget_resolver: malformed supported_node_types=%r for assignment=%s", supported, assign_id)

                        # Treat missing registry as a skip only when we have DB access
                        # AND the assignment provides no usable metadata. If the
                        # assignment itself contains component_type/configuration
                        # or an explicit id/name, accept it even when the registry
                        # lookup failed. This makes legacy JSON assignments visible
                        # when registry entries are missing or duplicated.
                        if not reg_info.get("found"):
                            has_assignment_metadata = bool(
                                w.get("component_type") or w.get("configuration") or w.get("id") or w.get("name")
                            )
                            if has_db and not has_assignment_metadata:
                                skip_reasons.append("skipped_missing_registry")

                        # If disabled or other skip reasons exist, log and continue
                        if skip_reasons:
                            logger.info(
                                "widget_resolver: assignment_decision node=%s assignment_id=%s decision=skipped reasons=%s",
                                n.id,
                                assign_id,
                                skip_reasons,
                            )
                            # If disabled, also ensure removal from effective_map if present
                            if "skipped_disabled" in skip_reasons:
                                try:
                                    effective_map.pop(assign_id, None)
                                    order = [e for e in order if widget_key(e.item) != str(assign_id)]
                                except Exception:
                                    pass
                            continue

                        # Enrich with registry metadata when available
                        try:
                            if reg_entry is not None:
                                md = getattr(reg_entry, "widget_metadata", None)
                                if md is None:
                                    md = getattr(reg_entry, "metadata", None)
                                if isinstance(md, str):
                                    try:
                                        md = json.loads(md)
                                    except Exception:
                                        md = {}
                                md = md or {}
                                comp = md.get("component_type") or getattr(reg_entry, "type", None)
                                if comp:
                                    w["component_type"] = comp
                                if not w.get("id"):
                                    w["id"] = getattr(reg_entry, "name", None) or getattr(reg_entry, "id", None)
                                if not w.get("name"):
                                    w["name"] = getattr(reg_entry, "name", None)
                                if not w.get("type"):
                                    w["type"] = getattr(reg_entry, "type", None)
                        except Exception:
                            logger.debug("widget_resolver: failed to enrich assignment with registry metadata for %s", assign_id)

                        # Final decision: include
                        logger.info("widget_resolver: assignment_decision node=%s assignment_id=%s decision=included final_id=%s component_type=%s", n.id, assign_id, w.get("id"), w.get("component_type"))

                        resolved = ResolvedWidget(item=w, source="assignment", source_node_id=n.id)
                        effective_map[widget_key(w)] = resolved
                        order = [e for e in order if widget_key(e.item) != widget_key(w)]
                        order.append(resolved)
                    except Exception:
                        logger.exception("Failed to process assignment on node %s", n.id)

        # Now produce output list sorted by position
        def pos_of(r: ResolvedWidget) -> int:
            try:
                return int(r.item.get("position", 1000) or 1000)
            except Exception:
                return 1000

        final = sorted([r.item for r in order], key=pos_of)

        # Defensive enrichment: ensure each final item includes `component_type` when available
        # by consulting the registry as a best-effort fallback. This avoids losing the graphical
        # renderer when the assignment lacks explicit metadata but a registry entry exists.
        if has_db:
            try:
                for it in final:
                    try:
                        if it.get('component_type'):
                            continue
                        lookup_name = it.get('id') or it.get('name') or it.get('widget_id')
                        reg_entry = None
                        if lookup_name:
                            from sqlalchemy import or_

                            # Try to match registry by name OR id to cover stable-id canonical rows
                            stmt = select(WidgetRegistry).where(
                                or_(WidgetRegistry.name == lookup_name, WidgetRegistry.id == lookup_name)
                            )
                            res = await self._session.execute(stmt)
                            rows = res.scalars().all()
                            reg_entry = self._choose_registry_candidate(rows, lookup_name)
                        # fallback: try matching by registry.type
                        if reg_entry is None and it.get('type'):
                            stmt = select(WidgetRegistry).where(WidgetRegistry.type == it.get('type'))
                            res = await self._session.execute(stmt)
                            rows = res.scalars().all()
                            reg_entry = self._choose_registry_candidate(rows, None)

                        if reg_entry is not None:
                            md = getattr(reg_entry, 'widget_metadata', None) or getattr(reg_entry, 'metadata', None) or {}
                            if isinstance(md, str):
                                try:
                                    md = json.loads(md)
                                except Exception:
                                    md = {}
                            comp = md.get('component_type') or getattr(reg_entry, 'type', None)
                            if comp:
                                it['component_type'] = comp
                    except Exception:
                        logger.debug('widget_resolver: failed to fallback-enrich item=%r', it, exc_info=True)
            except Exception:
                logger.debug('widget_resolver: fallback enrichment failed', exc_info=True)

        return final
