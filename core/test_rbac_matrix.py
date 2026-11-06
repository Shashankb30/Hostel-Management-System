"""NFR-01 / SR-1: every role-protected page is checked for every role.

Complements UT_NFR_01 (which only tries a student on 7 URLs). The expected access
matrix below is the one printed in docs/SRS.md, Appendix 4.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Hostel, Student, UserAccount

S, W, A = UserAccount.ROLE_STUDENT, UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN

# url name -> roles allowed to GET it (routes without URL arguments only)
ACCESS = {
    'accounts:users': {A}, 'accounts:user_create': {A},
    'students:list': {A}, 'students:add': {A},
    'rooms:manage': {A}, 'rooms:add': {A}, 'rooms:vacancy': {A, W},
    'allocation:manage': {W}, 'allocation:waitlist': {W}, 'allocation:rules': {W},
    'allocation:report': {W}, 'allocation:my_room': {S},
    'fees:manage': {A}, 'fees:dues_report': {A}, 'fees:my_fees': {S},
    'complaints:my_complaints': {S}, 'complaints:manage': {W, A},
    'complaints:log_misconduct': {W, A}, 'complaints:rules': {W, A}, 'complaints:report': {W, A},
    'attendance:my_attendance': {S}, 'attendance:manage': {W, A}, 'attendance:report': {W, A},
    'visitors:log': {W, A}, 'visitors:add': {W, A}, 'visitors:report': {W, A},
    'leave:my_leaves': {S}, 'leave:apply': {S}, 'leave:review': {W, A}, 'leave:records': {W, A},
    'notices:board': {S, W, A}, 'notices:manage': {W, A}, 'notices:add': {W, A},
    'core:dashboard_student': {S}, 'core:dashboard_warden': {W}, 'core:dashboard_admin': {A},
}


class RoleAccessMatrixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        hostel = Hostel.objects.create(name='Matrix Hostel', code='MXH')
        cls.users = {}
        for role in (S, W, A):
            user = get_user_model().objects.create(username=f'matrix_{role}')
            user.set_unusable_password()
            user.save()
            account = UserAccount.objects.create(user=user, role=role, hostel=hostel)
            if role == S:  # student pages (leave, fees...) need a student profile
                Student.objects.create(user_account=account, hostel=hostel, roll_no='MX001',
                                       full_name='Matrix Student', phone='9876543210', course='CSE',
                                       year_of_study=1)
            cls.users[role] = user

    def test_every_route_enforces_its_roles(self):
        failures = []
        for name, allowed in ACCESS.items():
            url = reverse(name)
            for role in (S, W, A):
                self.client.force_login(self.users[role])
                status = self.client.get(url).status_code
                if role in allowed and status == 403:
                    failures.append(f'{role} wrongly refused on {name}')
                if role not in allowed and status != 403:
                    failures.append(f'{role} wrongly allowed on {name} (HTTP {status})')
        self.assertEqual(failures, [])

    def test_anonymous_users_never_get_a_protected_page(self):
        self.client.logout()
        failures = []
        for name in ACCESS:
            status = self.client.get(reverse(name)).status_code
            if status == 200:
                failures.append(f'anonymous got HTTP 200 on {name}')
        self.assertEqual(failures, [])
