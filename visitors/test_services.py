"""Tests for Visitor Management services (FR-08)."""
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.models import Student, UserAccount, VisitorLog
from core.seed import seed
from visitors import services


def past_time(days_ago, hour=10, minute=0):
    """Helper to return an aware datetime in the past."""
    day = timezone.localdate() - timedelta(days=days_ago)
    return timezone.make_aware(datetime(day.year, day.month, day.day, hour, minute))


class VisitorServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')

    # --- UT_23_Vis: Visitor check-in with timestamp ---
    def test_UT_23_Vis__check_in_creates_log_with_timestamp(self):
        """Ramesh Kumar visiting Arjun Rao gets a check-in timestamp and is saved."""
        before = timezone.now()
        log = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='GOVT-ID-1234',
            purpose='Parent visit',
            recorded_by=self.warden,
        )
        log.refresh_from_db()
        self.assertEqual(log.visitor_name, 'Ramesh Kumar')
        self.assertEqual(log.id_proof, 'GOVT-ID-1234')
        self.assertEqual(log.student, self.arjun)
        self.assertEqual(log.hostel, self.arjun.hostel)
        self.assertEqual(log.recorded_by, self.warden)
        self.assertTrue(before <= log.checked_in_at <= timezone.now())
        self.assertIsNone(log.checked_out_at)
        self.assertTrue(log.is_active)

    # --- UT_24_Vis: Reject check-in with missing mandatory details ---
    def test_UT_24_Vis__reject_missing_id_proof(self):
        """Blank ID proof shows a validation error and creates no log entry (UC-08 exception 3a)."""
        initial_count = VisitorLog.objects.count()
        with self.assertRaises(ValidationError) as ctx:
            services.check_in(
                student=self.arjun,
                visitor_name='Ramesh Kumar',
                id_proof='   ',
                recorded_by=self.warden,
            )
        self.assertIn('ID proof is required', str(ctx.exception))
        self.assertEqual(VisitorLog.objects.count(), initial_count)

    def test_UT_24_Vis__reject_missing_visitor_name(self):
        """Blank visitor name shows a validation error and creates no log entry."""
        initial_count = VisitorLog.objects.count()
        with self.assertRaises(ValidationError) as ctx:
            services.check_in(
                student=self.arjun,
                visitor_name='',
                id_proof='ID-999',
                recorded_by=self.admin,
            )
        self.assertIn('Visitor name is required', str(ctx.exception))
        self.assertEqual(VisitorLog.objects.count(), initial_count)

    def test_UT_24_Vis__reject_missing_student(self):
        """Missing student raises validation error."""
        with self.assertRaises(ValidationError):
            services.check_in(
                student=None,
                visitor_name='Visitor',
                id_proof='ID-999',
            )

    # --- IT_22_Vis: Visitor check-out updates the same log entry ---
    def test_IT_22_Vis__check_out_updates_same_entry_and_calculates_duration(self):
        """Check-out time saved on the active entry and visit duration is calculated."""
        check_in_time = past_time(1, 10, 0)
        check_out_time = past_time(1, 12, 30)

        log = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-123',
            recorded_by=self.warden,
            check_in_at=check_in_time,
        )
        self.assertIsNone(log.checked_out_at)

        updated_log = services.check_out(log, recorded_by=self.warden, check_out_at=check_out_time)
        self.assertEqual(updated_log.pk, log.pk)
        self.assertEqual(updated_log.checked_out_at, check_out_time)
        self.assertEqual(updated_log.duration, timedelta(hours=2, minutes=30))
        self.assertEqual(services.format_duration(log.checked_in_at, log.checked_out_at), '2 h 30 min')
        self.assertFalse(updated_log.is_active)

    # --- ST_16_Vis: Prevent double check-out ---
    def test_ST_16_Vis__prevent_double_checkout(self):
        """Second check-out attempt is blocked with clear message."""
        log = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-123',
            recorded_by=self.warden,
            check_in_at=past_time(1, 10, 0),
        )
        services.check_out(log, check_out_at=past_time(1, 11, 0))

        with self.assertRaises(ValidationError) as ctx:
            services.check_out(log, check_out_at=past_time(1, 12, 0))
        self.assertIn('Already checked out', str(ctx.exception))

    # --- IT_23_Vis: Link visitor log to the visited student ---
    def test_IT_23_Vis__visitor_log_linked_to_student(self):
        """Entry appears in Arjun Rao's visitor history."""
        log1 = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-123',
            recorded_by=self.warden,
        )
        log2 = services.check_in(
            student=self.divya,
            visitor_name='Anita Sharma',
            id_proof='ID-456',
            recorded_by=self.warden,
        )

        arjun_history = services.get_student_visitor_history(self.arjun)
        self.assertIn(log1, arjun_history)
        self.assertNotIn(log2, arjun_history)

    # --- IT_24_Vis: Search visitor logs by student or date ---
    def test_IT_24_Vis__search_visitor_logs_by_student_or_date(self):
        """Searching 'Arjun Rao' returns only matching entries; date filter supported."""
        day1 = timezone.localdate() - timedelta(days=2)
        day2 = timezone.localdate() - timedelta(days=1)

        log1 = services.check_in(
            student=self.arjun,
            visitor_name='Ramesh Kumar',
            id_proof='ID-123',
            recorded_by=self.warden,
            check_in_at=past_time(2, 10, 0),
        )
        log2 = services.check_in(
            student=self.divya,
            visitor_name='Suresh Patel',
            id_proof='ID-456',
            recorded_by=self.warden,
            check_in_at=past_time(1, 11, 0),
        )

        # Search by student name
        results = services.search_visitors(query='Arjun Rao')
        self.assertIn(log1, results)
        self.assertNotIn(log2, results)

        # Search by date
        results_date1 = services.search_visitors(date=day1)
        self.assertIn(log1, results_date1)
        self.assertNotIn(log2, results_date1)

        results_date2 = services.search_visitors(date=day2)
        self.assertIn(log2, results_date2)
        self.assertNotIn(log1, results_date2)

    # --- ST_15_Vis: Visitor report for a date range ---
    def test_ST_15_Vis__visitor_report_date_range(self):
        """Report lists all visitor entries with check-in/out times in the range."""
        d1 = timezone.localdate() - timedelta(days=5)
        d2 = timezone.localdate() - timedelta(days=3)

        log1 = services.check_in(self.arjun, 'Visitor 1', 'ID-1', check_in_at=past_time(5, 10))
        log2 = services.check_in(self.arjun, 'Visitor 2', 'ID-2', check_in_at=past_time(3, 10))
        log3 = services.check_in(self.divya, 'Visitor 3', 'ID-3', check_in_at=past_time(1, 10))

        # Filter between d1 and d2
        report = services.visitor_report(from_date=d1, to_date=d2)
        self.assertIn(log1, report)
        self.assertIn(log2, report)
        self.assertNotIn(log3, report)
