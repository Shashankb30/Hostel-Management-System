"""Integration and view tests for Home / Long-Leave Application (FR-09)."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from core.models import LeaveApplication, Student, UserAccount
from core.seed import seed
from leave import services


class LeaveViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')

    # --- UT_25_Leave: Verify student can submit a leave application with valid dates ---
    def test_UT_25_Leave__student_submit_valid_application(self):
        """Student submits From: 10-Sep-2026, To: 15-Sep-2026, Reason: 'Festival' -> saved as 'Pending'."""
        self.client.login(username='stu1023', password='Pass@123')
        response = self.client.post(reverse('leave:apply'), {
            'from_date': '2026-09-10',
            'to_date': '2026-09-15',
            'reason': 'Festival',
            'destination': 'Home Town',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('leave:my_leaves'))
        self.assertContains(response, 'submitted successfully')

        app = LeaveApplication.objects.get(student=self.arjun, reason='Festival')
        self.assertEqual(app.from_date, date(2026, 9, 10))
        self.assertEqual(app.to_date, date(2026, 9, 15))
        self.assertEqual(app.status, LeaveApplication.STATUS_PENDING)

    # --- UT_26_Leave: Verify leave submission fails when end date precedes start date ---
    def test_UT_26_Leave__end_date_before_start_date_fails(self):
        """From 15-Sep-2026, To 10-Sep-2026 displays validation error and blocks submission."""
        self.client.login(username='stu1023', password='Pass@123')
        initial_count = LeaveApplication.objects.count()

        response = self.client.post(reverse('leave:apply'), {
            'from_date': '2026-09-15',
            'to_date': '2026-09-10',
            'reason': 'Festival',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'To date cannot be before From date')
        self.assertEqual(LeaveApplication.objects.count(), initial_count)

    # --- UT_27_Leave: Verify leave submission fails with missing reason ---
    def test_UT_27_Leave__missing_reason_fails(self):
        """Blank reason displays validation error and blocks submission."""
        self.client.login(username='stu1023', password='Pass@123')
        initial_count = LeaveApplication.objects.count()

        response = self.client.post(reverse('leave:apply'), {
            'from_date': '2026-09-10',
            'to_date': '2026-09-15',
            'reason': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reason is required')
        self.assertEqual(LeaveApplication.objects.count(), initial_count)

    # --- IT_25_Leave: Verify warden can approve a pending leave application ---
    def test_IT_25_Leave__warden_approve_application(self):
        """Warden opens application and clicks Approve -> Status updates to 'Approved'; student notified."""
        app = services.submit_leave_application(self.arjun, date(2026, 9, 10), date(2026, 9, 15), 'Festival')

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.post(reverse('leave:review_detail', args=[app.pk]), {
            'action': 'approve',
            'remarks': 'Approved by warden',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('leave:review'))
        self.assertContains(response, 'approved')

        app.refresh_from_db()
        self.assertEqual(app.status, LeaveApplication.STATUS_APPROVED)
        self.assertEqual(app.reviewed_by, self.warden)

    # --- IT_26_Leave: Verify warden can reject a pending leave application with remarks ---
    def test_IT_26_Leave__warden_reject_application_with_remarks(self):
        """Warden enters rejection remarks 'Insufficient notice' and clicks Reject -> Status updates to 'Rejected'."""
        app = services.submit_leave_application(self.arjun, date(2026, 9, 10), date(2026, 9, 15), 'Festival')

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.post(reverse('leave:review_detail', args=[app.pk]), {
            'action': 'reject',
            'remarks': 'Insufficient notice',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('leave:review'))
        self.assertContains(response, 'rejected')

        app.refresh_from_db()
        self.assertEqual(app.status, LeaveApplication.STATUS_REJECTED)
        self.assertEqual(app.reviewer_remarks, 'Insufficient notice')

    # --- IT_27_Leave: Verify overlapping leave dates are flagged for reviewer ---
    def test_IT_27_Leave__flag_overlapping_leave_dates_in_review_screen(self):
        """System flags the date conflict for the reviewer before approval."""
        app1 = services.submit_leave_application(self.arjun, date(2026, 9, 10), date(2026, 9, 15), 'Trip 1')
        services.approve_application(app1, reviewer=self.warden)

        # Overlapping application: 12-Sep to 18-Sep
        app2 = services.submit_leave_application(self.arjun, date(2026, 9, 12), date(2026, 9, 18), 'Trip 2')

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.get(reverse('leave:review_detail', args=[app2.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Warning: Overlapping Approved Leave Detected!')
        self.assertContains(response, app1.application_id)

    # --- ST_17_Leave: Verify leave application history is visible to the student ---
    def test_ST_17_Leave__student_leave_history_screen(self):
        """Student navigates to My Leave Applications -> all past and current applications display with correct status."""
        services.submit_leave_application(self.arjun, date(2026, 8, 1), date(2026, 8, 5), 'Past approved')
        app_past = LeaveApplication.objects.latest('created_at')
        services.approve_application(app_past, reviewer=self.warden)

        services.submit_leave_application(self.arjun, date(2026, 9, 10), date(2026, 9, 15), 'Upcoming pending')

        self.client.login(username='stu1023', password='Pass@123')
        response = self.client.get(reverse('leave:my_leaves'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Past approved')
        self.assertContains(response, 'Approved')
        self.assertContains(response, 'Upcoming pending')
        self.assertContains(response, 'Pending')

    # --- ST_18_Leave: Verify administrator can view leave records across all students ---
    def test_ST_18_Leave__admin_consolidated_records_screen(self):
        """Administrator navigates to Leave Records -> all students' leave applications are listed."""
        services.submit_leave_application(self.arjun, date(2026, 9, 10), date(2026, 9, 15), 'Arjun Leave')
        services.submit_leave_application(self.divya, date(2026, 9, 12), date(2026, 9, 16), 'Divya Leave')

        self.client.login(username='admin01', password='Admin@12')
        response = self.client.get(reverse('leave:records'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Arjun Rao')
        self.assertContains(response, 'Arjun Leave')
        self.assertContains(response, 'Divya S.')
        self.assertContains(response, 'Divya Leave')

    # --- Access control tests ---
    def test_student_cannot_access_staff_review(self):
        """Student receives 403 on staff review screen."""
        self.client.login(username='stu1023', password='Pass@123')
        response = self.client.get(reverse('leave:review'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_to_login(self):
        """Unauthenticated user redirected to login."""
        response = self.client.get(reverse('leave:my_leaves'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])
