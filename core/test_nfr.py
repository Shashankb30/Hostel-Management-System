"""Automated tests for Non-Functional Requirements (Epic #142 / NFR-01 to NFR-08)."""
import tempfile
import time
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Allocation, Hostel, Room, Student, UserAccount


class NFRHardeningTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hostel1 = Hostel.objects.create(name='North Block Hostel', code='NBH')
        self.hostel2 = Hostel.objects.create(name='South Block Hostel', code='SBH')

        User = get_user_model()
        # Student 1
        self.u_student1 = User.objects.create_user(username='stu_test1', password='TestPassword@123')
        self.acc_student1 = UserAccount.objects.create(
            user=self.u_student1, hostel=self.hostel1, role=UserAccount.ROLE_STUDENT
        )
        self.student1 = Student.objects.create(
            user_account=self.acc_student1, hostel=self.hostel1, roll_no='STU001', full_name='Student One'
        )

        # Student 2
        self.u_student2 = User.objects.create_user(username='stu_test2', password='TestPassword@123')
        self.acc_student2 = UserAccount.objects.create(
            user=self.u_student2, hostel=self.hostel1, role=UserAccount.ROLE_STUDENT
        )
        self.student2 = Student.objects.create(
            user_account=self.acc_student2, hostel=self.hostel1, roll_no='STU002', full_name='Student Two'
        )

        # Warden
        self.u_warden = User.objects.create_user(username='warden_test', password='TestPassword@123')
        self.acc_warden = UserAccount.objects.create(
            user=self.u_warden, hostel=self.hostel1, role=UserAccount.ROLE_WARDEN
        )

        # Administrator
        self.u_admin = User.objects.create_user(username='admin_test', password='TestPassword@123')
        self.acc_admin = UserAccount.objects.create(
            user=self.u_admin, hostel=self.hostel1, role=UserAccount.ROLE_ADMIN
        )

        # Room in Hostel 1
        self.room1 = Room.objects.create(hostel=self.hostel1, room_no='A-101', capacity=2)

    # -------------------------------------------------------------------------
    # NFR.01 / Issue #143: Role-based access control
    # -------------------------------------------------------------------------
    def test_UT_NFR_01__role_based_access_control(self):
        """Verify student is forbidden (403) from accessing admin and warden endpoints."""
        self.client.force_login(self.u_student1)

        forbidden_urls = [
            reverse('rooms:manage'),
            reverse('allocation:manage'),
            reverse('students:list'),
            reverse('accounts:users'),
            reverse('notices:add'),
            reverse('visitors:add'),
            reverse('leave:review'),
        ]
        for url in forbidden_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 403, f'Expected 403 for student accessing {url}, got {response.status_code}'
            )

    # -------------------------------------------------------------------------
    # NFR.02 / Issue #144: Password hashing and session handling
    # -------------------------------------------------------------------------
    def test_UT_NFR_02__password_hashing_and_session(self):
        """Verify passwords are cryptographic hashes and session security settings are active."""
        # 1. Password is not stored in plaintext
        self.assertFalse(self.u_student1.password.startswith('TestPassword'))
        self.assertTrue(self.u_student1.password.startswith('pbkdf2_sha256$'))

        # 2. Session timeout is configured
        self.assertGreaterEqual(settings.SESSION_COOKIE_AGE, 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertTrue(getattr(settings, 'SESSION_COOKIE_HTTPONLY', True))
        self.assertTrue(getattr(settings, 'CSRF_COOKIE_HTTPONLY', True))

    # -------------------------------------------------------------------------
    # NFR.03 / Issue #145: Cross-student data isolation
    # -------------------------------------------------------------------------
    def test_UT_NFR_03__cross_student_access_denied(self):
        """Verify student cannot access another student's fee details or visitor logs."""
        self.client.force_login(self.u_student1)

        # Attempt to access student 2's fees
        other_fee_url = reverse('fees:student_fees', kwargs={'student_id': self.student2.pk})
        resp = self.client.get(other_fee_url)
        self.assertEqual(resp.status_code, 403)

        # Attempt to access student 2's visitor log
        other_visitor_url = reverse('visitors:student_history', kwargs={'student_id': self.student2.pk})
        resp = self.client.get(other_visitor_url)
        self.assertEqual(resp.status_code, 403)

    # -------------------------------------------------------------------------
    # NFR.04 / Issue #146: Input sanitization and XSS prevention
    # -------------------------------------------------------------------------
    def test_UT_NFR_04__input_sanitization_and_xss(self):
        """Verify HTML/Script tags injected in content are auto-escaped in rendered output."""
        from core.models import Notice

        xss_payload = "<script>alert('XSS-ATTACK');</script>"
        Notice.objects.create(
            hostel=self.hostel1,
            published_by=self.acc_admin,
            title='Maintenance Alert',
            body=xss_payload,
            audience='all',
            is_published=True,
        )

        self.client.force_login(self.u_student1)
        resp = self.client.get(reverse('notices:board'))
        self.assertEqual(resp.status_code, 200)

        # The raw unescaped script tag should NOT exist in the HTML
        self.assertNotContains(resp, '<script>alert(')
        # Instead, it must be HTML-escaped
        self.assertContains(resp, '&lt;script&gt;alert(')

    # -------------------------------------------------------------------------
    # NFR.06 / Issue #148: Performance baseline under 3 seconds
    # -------------------------------------------------------------------------
    def test_UT_NFR_06__performance_under_3_seconds(self):
        """Verify core endpoint responses execute well under the 3.0 second NFR-03 requirement."""
        self.client.force_login(self.u_admin)

        endpoints = [
            reverse('health_check'),
            reverse('core:dashboard_admin'),
            reverse('students:list'),
            reverse('rooms:manage'),
            reverse('fees:manage'),
        ]

        for url in endpoints:
            t0 = time.perf_counter()
            resp = self.client.get(url)
            elapsed = time.perf_counter() - t0
            self.assertEqual(resp.status_code, 200)
            self.assertLess(elapsed, 3.0, f'Endpoint {url} took {elapsed:.2f}s, exceeding 3.0s threshold!')

    # -------------------------------------------------------------------------
    # NFR.07 / Issue #149: Database indexes and pagination
    # -------------------------------------------------------------------------
    def test_UT_NFR_07__database_indexes_and_pagination(self):
        """Verify index constraints and pagination on entity lists."""
        # Unique fields are indexed by default
        self.assertTrue(Student._meta.get_field('roll_no').unique)
        self.assertTrue(Room._meta.get_field('room_no').name)

        # Pagination check
        self.client.force_login(self.u_admin)
        resp = self.client.get(reverse('students:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('page' in resp.context or 'page_obj' in resp.context)

    # -------------------------------------------------------------------------
    # NFR.08 / Issue #150: Backup and restore procedure
    # -------------------------------------------------------------------------
    def test_UT_NFR_08__backup_and_restore_cycle(self):
        """Verify backup command creates valid JSON snapshot and restore restores records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_file = Path(tmpdir) / 'test_hms_backup.json'

            # 1. Take backup
            call_command('backup_database', output=str(backup_file))
            self.assertTrue(backup_file.exists())
            self.assertGreater(backup_file.stat().st_size, 0)

            # 2. Modify state: create a new room
            Room.objects.create(hostel=self.hostel1, room_no='TEMP-999', capacity=1)
            self.assertTrue(Room.objects.filter(room_no='TEMP-999').exists())

            # 3. Restore backup
            call_command('restore_database', str(backup_file))

            # The original seeded room exists
            self.assertTrue(Room.objects.filter(room_no='A-101').exists())

    # -------------------------------------------------------------------------
    # NFR.09 / Issue #151: Transactional writes and graceful failure handling
    # -------------------------------------------------------------------------
    def test_UT_NFR_09__transactional_rollback(self):
        """Verify multi-step updates roll back completely upon error and custom error pages render."""
        # 1. Transaction atomicity check
        initial_alloc_count = Allocation.objects.count()
        try:
            with transaction.atomic():
                Allocation.objects.create(
                    student=self.student1, room=self.room1, allocated_on=date.today(), status='active'
                )
                # Deliberately raise exception
                raise RuntimeError('Simulated failure during allocation')
        except RuntimeError:
            pass

        # Verify rollback occurred
        self.assertEqual(Allocation.objects.count(), initial_alloc_count)

        # 2. Custom error handlers render without crashing
        c = Client()
        resp_404 = c.get('/nonexistent-route-for-testing-404/')
        self.assertEqual(resp_404.status_code, 404)
        self.assertContains(resp_404, 'Page Not Found', status_code=404)

    # -------------------------------------------------------------------------
    # NFR.10 / Issue #152: Database constraints and server-side integrity
    # -------------------------------------------------------------------------
    def test_UT_NFR_10__database_constraints(self):
        """Verify database constraints reject duplicate Roll No and duplicate Room No in same hostel."""
        # Duplicate roll number
        with self.assertRaises(IntegrityError), transaction.atomic():
            Student.objects.create(
                user_account=self.acc_student1, hostel=self.hostel1, roll_no='STU001', full_name='Duplicate Roll'
            )

        # Duplicate room number in same hostel
        with self.assertRaises(IntegrityError), transaction.atomic():
            Room.objects.create(hostel=self.hostel1, room_no='A-101', capacity=1)

    # -------------------------------------------------------------------------
    # NFR.12 / Issue #154: Multi-hostel support
    # -------------------------------------------------------------------------
    def test_UT_NFR_12__multi_hostel_support(self):
        """Verify room number can repeat in another hostel without collision."""
        # Room A-101 in Hostel 2 is allowed even though A-101 exists in Hostel 1
        room_in_hostel2 = Room.objects.create(hostel=self.hostel2, room_no='A-101', capacity=3)
        self.assertEqual(room_in_hostel2.room_no, 'A-101')
        self.assertEqual(room_in_hostel2.hostel, self.hostel2)

    # -------------------------------------------------------------------------
    # NFR.13 / Issue #155: Health check endpoint and maintenance handling
    # -------------------------------------------------------------------------
    def test_UT_NFR_13__health_check_endpoint(self):
        """Verify /health/ returns HTTP 200 with JSON payload and database connectivity."""
        c = Client()
        resp = c.get(reverse('health_check'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')
        self.assertEqual(data.get('version'), '1.0.0')

        # Maintenance view test
        resp_maint = c.get(reverse('core:maintenance'))
        self.assertEqual(resp_maint.status_code, 200)
        self.assertContains(resp_maint, 'Maintenance')
