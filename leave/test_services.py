"""Unit tests for Leave Management services (FR-09)."""
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import LeaveApplication, Notification, Student, UserAccount
from core.seed import seed
from leave import services


class LeaveServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')

    # --- UT_25_Leave: Verify student can submit a leave application with valid dates ---
    def test_UT_25_Leave__submit_valid_leave_application(self):
        """Student submits with valid dates and reason; saved with status 'Pending'."""
        app = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 10),
            to_date=date(2026, 9, 15),
            reason='Festival',
            destination='Home Town',
        )
        app.refresh_from_db()
        self.assertEqual(app.student, self.arjun)
        self.assertEqual(app.hostel, self.arjun.hostel)
        self.assertEqual(app.from_date, date(2026, 9, 10))
        self.assertEqual(app.to_date, date(2026, 9, 15))
        self.assertEqual(app.reason, 'Festival')
        self.assertEqual(app.destination, 'Home Town')
        self.assertEqual(app.status, LeaveApplication.STATUS_PENDING)
        self.assertEqual(app.application_id, f'LV-{app.pk:03d}')

    # --- UT_26_Leave: Verify leave submission fails when end date precedes start date ---
    def test_UT_26_Leave__reject_end_date_before_start_date(self):
        """From 15-Sep to 10-Sep is rejected with validation error."""
        with self.assertRaises(ValidationError) as ctx:
            services.submit_leave_application(
                student=self.arjun,
                from_date=date(2026, 9, 15),
                to_date=date(2026, 9, 10),
                reason='Festival',
            )
        self.assertIn('To date cannot be before From date', str(ctx.exception))

    # --- UT_27_Leave: Verify leave submission fails with missing reason ---
    def test_UT_27_Leave__reject_blank_reason(self):
        """Blank reason shows a validation error and blocks submission."""
        initial_count = LeaveApplication.objects.count()
        with self.assertRaises(ValidationError) as ctx:
            services.submit_leave_application(
                student=self.arjun,
                from_date=date(2026, 9, 10),
                to_date=date(2026, 9, 15),
                reason='   ',
            )
        self.assertIn('Reason is required', str(ctx.exception))
        self.assertEqual(LeaveApplication.objects.count(), initial_count)

    # --- IT_25_Leave: Verify warden can approve a pending leave application ---
    def test_IT_25_Leave__warden_approves_pending_application(self):
        """Status updates to 'Approved'; student is notified."""
        app = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 10),
            to_date=date(2026, 9, 15),
            reason='Festival',
        )
        approved = services.approve_application(app, reviewer=self.warden, remarks='Have a safe trip')
        approved.refresh_from_db()

        self.assertEqual(approved.status, LeaveApplication.STATUS_APPROVED)
        self.assertEqual(approved.reviewed_by, self.warden)
        self.assertIsNotNone(approved.reviewed_at)
        self.assertEqual(approved.reviewer_remarks, 'Have a safe trip')

        # Check notification
        notif = Notification.objects.filter(recipient=self.arjun.user_account).latest('created_at')
        self.assertEqual(notif.category, Notification.CATEGORY_LEAVE)
        self.assertIn('approved', notif.message)

    # --- IT_26_Leave: Verify warden can reject a pending leave application with remarks ---
    def test_IT_26_Leave__warden_rejects_with_remarks(self):
        """Status updates to 'Rejected'; remarks visible and student notified."""
        app = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 10),
            to_date=date(2026, 9, 15),
            reason='Festival',
        )
        rejected = services.reject_application(app, reviewer=self.warden, remarks='Insufficient notice')
        rejected.refresh_from_db()

        self.assertEqual(rejected.status, LeaveApplication.STATUS_REJECTED)
        self.assertEqual(rejected.reviewer_remarks, 'Insufficient notice')
        self.assertEqual(rejected.reviewed_by, self.warden)

        notif = Notification.objects.filter(recipient=self.arjun.user_account).latest('created_at')
        self.assertEqual(notif.category, Notification.CATEGORY_LEAVE)
        self.assertIn('rejected', notif.message)
        self.assertIn('Insufficient notice', notif.message)

    def test_IT_26_Leave__reject_without_remarks_fails(self):
        """Rejection remarks are mandatory."""
        app = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 10),
            to_date=date(2026, 9, 15),
            reason='Festival',
        )
        with self.assertRaises(ValidationError) as ctx:
            services.reject_application(app, reviewer=self.warden, remarks='   ')
        self.assertIn('Rejection remarks is required', str(ctx.exception))

    # --- IT_27_Leave: Verify overlapping leave dates are flagged ---
    def test_IT_27_Leave__flag_overlapping_leave_dates(self):
        """12-18 Sep against an approved 10-15 Sep is flagged before approval (UC-09 exception 3a)."""
        app1 = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 10),
            to_date=date(2026, 9, 15),
            reason='Festival Part 1',
        )
        services.approve_application(app1, reviewer=self.warden)

        app2 = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 12),
            to_date=date(2026, 9, 18),
            reason='Festival Part 2',
        )
        overlaps = services.get_overlapping_leaves(app2)
        self.assertIn(app1, overlaps)

        # Divya's leave should not overlap with Arjun's
        app_divya = services.submit_leave_application(
            student=self.divya,
            from_date=date(2026, 9, 12),
            to_date=date(2026, 9, 18),
            reason='Divya trip',
        )
        self.assertEqual(services.get_overlapping_leaves(app_divya).count(), 0)

    # --- FR-09.08: Request more information from student and resubmit ---
    def test_FR_09_08__request_more_info_and_resubmit(self):
        """Warden requests more info, student updates and resubmits."""
        app = services.submit_leave_application(
            student=self.arjun,
            from_date=date(2026, 9, 10),
            to_date=date(2026, 9, 15),
            reason='Family function',
        )
        services.request_more_information(app, reviewer=self.warden, remarks='Attach invitation or specify relation')
        app.refresh_from_db()
        self.assertEqual(app.status, LeaveApplication.STATUS_INFO_REQUESTED)
        self.assertEqual(app.reviewer_remarks, 'Attach invitation or specify relation')

        # Student updates and resubmits
        resubmitted = services.resubmit_application(
            app,
            reason='Sister wedding in Mumbai',
            destination='Mumbai',
        )
        resubmitted.refresh_from_db()
        self.assertEqual(resubmitted.status, LeaveApplication.STATUS_PENDING)
        self.assertEqual(resubmitted.reason, 'Sister wedding in Mumbai')
        self.assertEqual(resubmitted.destination, 'Mumbai')

    # --- ST_17_Leave: Student leave application history ---
    def test_ST_17_Leave__student_leave_history(self):
        """All applications for student are listed."""
        app1 = services.submit_leave_application(self.arjun, date(2026, 9, 1), date(2026, 9, 3), 'Leave 1')
        app2 = services.submit_leave_application(self.arjun, date(2026, 9, 10), date(2026, 9, 15), 'Leave 2')
        app_divya = services.submit_leave_application(self.divya, date(2026, 9, 1), date(2026, 9, 3), 'Divya Leave')

        arjun_history = services.get_student_leaves(self.arjun)
        self.assertIn(app1, arjun_history)
        self.assertIn(app2, arjun_history)
        self.assertNotIn(app_divya, arjun_history)

    # --- ST_18_Leave: Administrator consolidated leave records ---
    def test_ST_18_Leave__consolidated_records(self):
        """Lists status and dates across all students."""
        app1 = services.submit_leave_application(self.arjun, date(2026, 9, 1), date(2026, 9, 3), 'Leave 1')
        app2 = services.submit_leave_application(self.divya, date(2026, 9, 5), date(2026, 9, 8), 'Leave 2')

        all_leaves = services.get_all_leaves()
        self.assertIn(app1, all_leaves)
        self.assertIn(app2, all_leaves)
