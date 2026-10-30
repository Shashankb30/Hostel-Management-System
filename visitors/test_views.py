"""Integration and view tests for Visitor Management (FR-08)."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Student, UserAccount, VisitorLog
from core.seed import seed
from visitors import services


class VisitorViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')
        cls.student_acc = UserAccount.objects.get(user__username='stu1023')

    # --- UT_22_Vis: Verify Add Visitor form captures required details ---
    def test_UT_22_Vis__add_visitor_form_displays_required_fields(self):
        """Form displays fields for visitor name, ID proof, purpose, and student visited."""
        self.client.login(username='admin01', password='Admin@12')
        response = self.client.get(reverse('visitors:add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visitor Name')
        self.assertContains(response, 'ID Proof')
        self.assertContains(response, 'Purpose')
        self.assertContains(response, 'Student Visited')

        # Warden can also record visitors
        self.client.logout()
        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.get(reverse('visitors:add'))
        self.assertEqual(response.status_code, 200)

    # --- UT_23_Vis: Verify successful visitor check-in is recorded with timestamp ---
    def test_UT_23_Vis__successful_visitor_checkin_recorded_with_timestamp(self):
        """Visitor: Ramesh Kumar, Student visited: Arjun Rao -> Visitor entry is created with timestamp."""
        self.client.login(username='admin01', password='Admin@12')
        response = self.client.post(reverse('visitors:add'), {
            'visitor_name': 'Ramesh Kumar',
            'id_proof': 'AADHAAR-8821',
            'student': self.arjun.pk,
            'purpose': 'Parent visit',
            'visitor_phone': '9876543210',
        }, follow=True)

        self.assertRedirects(response, reverse('visitors:log'))
        self.assertContains(response, 'Ramesh Kumar')
        self.assertContains(response, 'checked in successfully')

        log = VisitorLog.objects.get(visitor_name='Ramesh Kumar', student=self.arjun)
        self.assertEqual(log.id_proof, 'AADHAAR-8821')
        self.assertIsNotNone(log.checked_in_at)
        self.assertIsNone(log.checked_out_at)

    # --- UT_24_Vis: Verify visitor check-in fails with missing ID proof ---
    def test_UT_24_Vis__missing_id_proof_displays_validation_error(self):
        """Leave ID proof blank -> validation error and blocks check-in; no log entry is created."""
        self.client.login(username='admin01', password='Admin@12')
        initial_count = VisitorLog.objects.count()

        response = self.client.post(reverse('visitors:add'), {
            'visitor_name': 'Ramesh Kumar',
            'id_proof': '',
            'student': self.arjun.pk,
            'purpose': 'Parent visit',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ID proof is required')
        self.assertEqual(VisitorLog.objects.count(), initial_count)

    # --- IT_22_Vis: Verify visitor check-out updates the same visitor's log entry ---
    def test_IT_22_Vis__visitor_checkout_updates_active_entry(self):
        """Check-out time is recorded on the same entry; visit duration is calculated."""
        log = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-1234',
            recorded_by=self.warden,
        )

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.post(reverse('visitors:checkout', args=[log.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'checked out')
        log.refresh_from_db()
        self.assertIsNotNone(log.checked_out_at)
        self.assertIsNotNone(log.duration)

    # --- ST_16_Vis: Verify a checked-out visitor entry cannot be checked out again ---
    def test_ST_16_Vis__prevent_duplicate_checkout(self):
        """System prevents duplicate check-out and displays an appropriate message."""
        log = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-1234',
            recorded_by=self.warden,
        )
        services.check_out(log, recorded_by=self.warden)
        original_checkout_time = log.checked_out_at

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.post(reverse('visitors:checkout', args=[log.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Already checked out')
        log.refresh_from_db()
        self.assertEqual(log.checked_out_at, original_checkout_time)

    # --- IT_23_Vis: Verify visitor log links correctly to the student being visited ---
    def test_IT_23_Vis__visitor_log_links_to_student_history(self):
        """Add visitor referencing Student 'Arjun Rao' -> appears in that student's visitor history."""
        services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-1234',
            recorded_by=self.warden,
        )

        self.client.login(username='admin01', password='Admin@12')
        response = self.client.get(reverse('visitors:student_history', args=[self.arjun.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramesh Kumar')
        self.assertContains(response, 'Arjun Rao')

    # --- IT_24_Vis: Verify visitor search by date or student name returns correct results ---
    def test_IT_24_Vis__search_by_student_name_or_date(self):
        """Searching 'Arjun Rao' returns only matching entries."""
        services.check_in(self.arjun, 'Ramesh Kumar', 'ID-1', recorded_by=self.warden)
        services.check_in(self.divya, 'Anita Sharma', 'ID-2', recorded_by=self.warden)

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.get(reverse('visitors:log'), {'q': 'Arjun Rao'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramesh Kumar')
        self.assertNotContains(response, 'Anita Sharma')

    # --- ST_15_Vis: Verify visitor log report can be exported/generated for a date range ---
    def test_ST_15_Vis__visitor_report_and_csv_export(self):
        """Report lists all visitor entries with check-in/out times within the range; report can be exported."""
        log = services.check_in(self.arjun, 'Ramesh Kumar', 'ID-1', recorded_by=self.admin)
        services.check_out(log, recorded_by=self.admin)

        today = timezone.localdate().strftime('%Y-%m-%d')
        self.client.login(username='admin01', password='Admin@12')

        # Web view
        response = self.client.get(reverse('visitors:report'), {'from_date': today, 'to_date': today})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ramesh Kumar')

        # CSV export
        export_resp = self.client.get(reverse('visitors:report'), {
            'from_date': today,
            'to_date': today,
            'export': 'csv',
        })
        self.assertEqual(export_resp.status_code, 200)
        self.assertEqual(export_resp['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="visitor_report.csv"', export_resp['Content-Disposition'])
        content = export_resp.content.decode('utf-8')
        self.assertIn('Visitor Name', content)
        self.assertIn('Ramesh Kumar', content)
        self.assertIn('Arjun Rao', content)

    # --- Role authorization checks ---
    def test_student_cannot_access_staff_visitor_endpoints(self):
        """Student gets 403 on staff-only visitor endpoints."""
        self.client.login(username='stu1023', password='Pass@123')
        resp = self.client.get(reverse('visitors:log'))
        self.assertEqual(resp.status_code, 403)
        resp2 = self.client.get(reverse('visitors:add'))
        self.assertEqual(resp2.status_code, 403)

    def test_anonymous_redirected_to_login(self):
        """Unauthenticated user is redirected to login."""
        resp = self.client.get(reverse('visitors:log'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp['Location'])
