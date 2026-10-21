from .navigation import build_menu
from .roles import ROLE_LABELS, get_role


def navigation(request):
    """Make the role and the role's menu available to every template."""
    role = get_role(getattr(request, 'user', None))
    if role is None:
        return {}
    return {
        'hms_role': role,
        'hms_role_label': ROLE_LABELS.get(role, role.title()),
        'nav_items': build_menu(role, request.path),
    }
