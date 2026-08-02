# Review- und TODO-Liste: Konfigurations-Definitionsänderungen

Kurznotiz zu den Änderungen, die während der Settings-v2-Migration vorgenommen wurden,
und Punkte, die ein Maintainer überprüfen sollte.

## Entfernt / Ersetzt

- `general.default_language` — entfernt; verwende stattdessen `identity.default_language`.
- `models.default_model_id` — entfernt; die Codebasis verwendet `models.default_model` als
  reichhaltigere und bevorzugte Definition.

## Umbenannt

- `planning.quality_check` → `planning.quality_check_enabled` (Name an Katalog angepasst).

## Lokal (nicht in CONFIG_DEFINITIONS)

- `appearance.density` bleibt eine `LOCAL_PREFERENCE`-Einstellung und ist deshalb
  bewusst nicht in `CONFIG_DEFINITIONS` aufgenommen.

## Offene Review-Punkte

1. Platzhalter-Definitions: Viele konservative, generische Platzhalter wurden hinzugefügt,
   um das Fehlen von Keys im Katalog zu vermeiden. Bitte prüfen und ersetzen mit präzisen
   `value_schema`, `default_value`, `ui`-Metadaten und `permissions` — insbesondere für
   Gruppen: `knowledge`, `models`, `planning`, `tools`, `security`, `learning`.

2. `models.default_model` vs. `models.default_model_id`: Stelle sicher, dass alle Services
   (Model-Registry, Provider-Integration, Bootstrapping) die neue Namenswahl verwenden.

3. CI-Check: Füge `scripts/check_settings_defs.py` als CI-Job hinzu, damit Katalog und
   `CONFIG_DEFINITIONS` nicht wieder auseinanderlaufen.

4. Frontend-Save-Validation: Implementiere eine clientseitige Vorabprüfung, die verhindert,
   dass unbekannte/undefinierte Keys an `PUT /api/v1/config` gesendet werden.

## Referenzen

- Datei: `backend/app/config/definitions.py`
- Katalog: `backend/app/services/settings_catalog.py`
- Checker: `scripts/check_settings_defs.py`

---
Bitte prüfe die TODOs und sag Bescheid, ob ich die Platzhalter weiter präzisieren oder
ein PR mit diesen Änderungen erstellen soll.
