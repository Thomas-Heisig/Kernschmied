from app.auth.models import UserContext


def test_development_admin_permissions():
    dev = UserContext.development_admin()
    perms = set(dev.permissions)

    required = {
        "ui_schema.read",
        "hierarchy.read",
        "config.read",
        "models.read",
        "tools.read",
        "documentation.read",
    }

    # development_admin should include at least hierarchy.read, config.read, models.read, tools.read
    assert "hierarchy.read" in perms or any(p.endswith(":*") or p == "*" for p in perms)
    assert "config.read" in perms or any(p.endswith(":*") or p == "*" for p in perms)
    assert "models.read" in perms or any(p.endswith(":*") or p == "*" for p in perms)
    assert "tools.read" in perms or any(p.endswith(":*") or p == "*" for p in perms)
