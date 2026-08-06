from app.schemas.settings_catalog import (
    SettingsCatalogResponse,
    SettingsGroupDescriptor,
    SettingsSectionDescriptor,
)
from app.services.settings_catalog import build_settings_catalog


def test_settings_catalog_includes_authentication_section():
    catalog: SettingsCatalogResponse = build_settings_catalog()
    groups: dict[str, SettingsGroupDescriptor] = {g.id: g for g in catalog.groups}
    assert "security" in groups
    security: SettingsGroupDescriptor = groups["security"]
    sections: dict[str, SettingsSectionDescriptor] = {
        s.id: s for s in security.sections
    }
    assert "security.authentication" in sections
    auth_section: SettingsSectionDescriptor = sections["security.authentication"]
    field_ids: set[str] = {f.id for f in auth_section.fields}
    expected: set[str] = {
        "security.authentication.development_fallback",
        "security.authentication.development_admin_login_enabled",
        "security.authentication.self_registration_enabled",
        "security.authentication.development_self_registration_enabled",
        "security.authentication.registration_requires_invitation",
    }
    assert expected.issubset(field_ids)
