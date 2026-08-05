from app.auth.models import UserContext


def test_development_admin_permissions():
    dev = UserContext.development_admin()
    perms = set(dev.permissions)

    required = {
        "hierarchy.read",
        "config.read",
        "models.read",
        "tools.read",
    }

    # development_admin should include at least the required read permissions
    for req in required:
        assert req in perms or any(p.endswith(":*") or p == "*" for p in perms)
