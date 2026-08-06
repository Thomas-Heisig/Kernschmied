import pathlib


def test_migration_0013_exists_and_contains_authentication_method():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    migration = (
        repo_root
        / "migrations"
        / "versions"
        / "0013_add_authentication_method_to_auth_sessions.py"
    )
    assert migration.exists(), f"Migration file not found: {migration}"
    content = migration.read_text(encoding="utf-8")
    assert (
        "authentication_method" in content
    ), "Migration does not reference authentication_method"
