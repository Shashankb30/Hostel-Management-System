"""Role-based menus (Issue #12, SETUP.11).

Each module plugs into the shell by adding a URL with the name listed here.
Until that URL exists the menu item is shown greyed out ("Soon"), so the menu
never breaks and no shell code has to change when a module is delivered.
"""
from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse

from .models import UserAccount


@dataclass(frozen=True)
class NavItem:
    label: str
    url_name: str


MENUS = {
    UserAccount.ROLE_STUDENT: [
        NavItem('Dashboard', 'core:dashboard_student'),
        NavItem('My Profile', 'students:my_profile'),
        NavItem('My Room', 'allocation:my_room'),
        NavItem('Fees & Payments', 'fees:my_fees'),
        NavItem('Complaints', 'complaints:my_complaints'),
        NavItem('Attendance', 'attendance:my_attendance'),
        NavItem('Leave', 'leave:my_leaves'),
        NavItem('Notices', 'notices:board'),
    ],
    UserAccount.ROLE_WARDEN: [
        NavItem('Dashboard', 'core:dashboard_warden'),
        NavItem('Rooms & Vacancy', 'rooms:vacancy'),
        NavItem('Room Allocation', 'allocation:manage'),
        NavItem('Complaints', 'complaints:manage'),
        NavItem('Attendance', 'attendance:manage'),
        NavItem('Visitors', 'visitors:log'),
        NavItem('Leave Requests', 'leave:review'),
        NavItem('Notices', 'notices:manage'),
    ],
    UserAccount.ROLE_ADMIN: [
        NavItem('Dashboard', 'core:dashboard_admin'),
        NavItem('Users & Roles', 'accounts:users'),
        NavItem('Students', 'students:list'),
        NavItem('Rooms', 'rooms:manage'),
        NavItem('Fees', 'fees:manage'),
        NavItem('Attendance', 'attendance:manage'),
        NavItem('Notices', 'notices:manage'),
        NavItem('Reports', 'core:reports'),
        NavItem('Admin Site', 'admin:index'),
    ],
}


def build_menu(role, current_path=''):
    """Return the menu for a role as dicts: label, url (None if not built yet), active."""
    items = []
    for item in MENUS.get(role, []):
        try:
            url = reverse(item.url_name)
        except NoReverseMatch:
            url = None
        items.append({
            'label': item.label,
            'url': url,
            'active': bool(url) and current_path.startswith(url),
        })
    return items
