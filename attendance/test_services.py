"""FR-07 rules: check-in, check-out, bulk marking, daily summary, history and report."""
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.models import Allocation, AttendanceRecord, Hostel, Room, Student, UserAccount
from core.seed import seed

from . import services


def at(days_ago, hour, minute=0):
    """A local time on a day in the past, so it can never be 'in the future'."""
    day = timezone.localdate() - timedelta(days=days_ago)
    return timezone.make_aware(datetime(day.year, day.month, day.day, hour, minute))


class AttendanceServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.room = Room.objects.get(room_no='A-101')
        for student in (cls.arjun, cls.divya):
            Allocation.objects.create(student=student, room=cls.room, allocated_on=date(2026, 7, 1))

    def new_student(self, name, room=True, hostel=None):
        user = get_user_model().objects.create(username=f'user_{name}')
        account = UserAccount.objects.create(user=user, role='student', hostel=hostel or self.arjun.hostel)
        student = Student.objects.create(user_account=account, hostel=hostel or self.arjun.hostel,
                                         roll_no=f'R-{name}', full_name=name.title())
        if room:
            Allocation.objects.create(student=student, room=self.room, allocated_on=date(2026, 7, 1))
        return student

    def errors(self, call, *args, **kwargs):
        with self.assertRaises(ValidationError) as caught:
            call(*args, **kwargs)
        return caught.exception.messages

    # --- UT_19_Att: check-in --------------------------------------------------------------
    def test_ut_19_check_in_records_the_time_for_the_student(self):
        when = at(1, 20)                                                     # 08:00 PM
        record = services.check_in(self.divya, self.warden, when)
        record.refresh_from_db()
        self.assertEqual((record.student, record.hostel, record.recorded_by),
                         (self.divya, self.divya.hostel, self.warden))
        self.assertEqual(record.check_in_at, when)
        self.assertEqual(record.attendance_date, timezone.localdate() - timedelta(days=1))
        self.assertIsNone(record.check_out_at)

    def test_check_in_defaults_to_now(self):
        before = timezone.now()
        record = services.check_in(self.arjun, self.warden)
        self.assertTrue(before <= record.check_in_at <= timezone.now())
        self.assertEqual(record.attendance_date, timezone.localdate())

    def test_a_naive_time_is_treated_as_local_time(self):
        naive = datetime.combine(timezone.localdate() - timedelta(days=1), datetime.min.time()).replace(hour=20)
        record = services.check_in(self.arjun, self.warden, naive)
        self.assertEqual(timezone.localtime(record.check_in_at).hour, 20)

    def test_a_time_in_the_future_is_refused(self):
        future = timezone.now() + timedelta(hours=2)
        self.assertEqual(self.errors(services.check_in, self.arjun, self.warden, future), ['Time cannot be in the future'])
        self.assertFalse(AttendanceRecord.objects.exists())

    # --- FR-07.05: only students with a room ---------------------------------------------
    def test_a_student_without_a_room_cannot_be_checked_in(self):
        loose = self.new_student('loose', room=False)
        self.assertEqual(self.errors(services.check_in, loose, self.warden),
                         ['Attendance can only be recorded for students with an allocated room'])
        self.assertFalse(AttendanceRecord.objects.exists())

    def test_a_student_whose_room_was_released_cannot_be_checked_in(self):
        Allocation.objects.filter(student=self.arjun).update(status='ended', ended_on=date(2026, 9, 1))
        self.assertEqual(self.errors(services.check_in, self.arjun, self.warden),
                         ['Attendance can only be recorded for students with an allocated room'])

    def test_an_inactive_student_cannot_be_checked_in(self):
        Student.objects.filter(pk=self.arjun.pk).update(is_active=False)
        self.arjun.refresh_from_db()
        self.assertEqual(self.errors(services.check_in, self.arjun, self.warden), ['Student is inactive'])

    # --- UT_20_Att: check-out --------------------------------------------------------------
    def test_ut_20_check_out_completes_the_entry_even_the_next_morning(self):
        services.check_in(self.divya, self.warden, at(3, 20))                 # 08:00 PM
        entry = services.check_out(self.divya, self.warden, at(2, 9, 30))     # 09:30 AM next day
        entry.refresh_from_db()
        self.assertEqual(entry.check_out_at, at(2, 9, 30))
        self.assertEqual(entry.attendance_date, timezone.localdate() - timedelta(days=3))
        self.assertEqual(AttendanceRecord.objects.count(), 1)
        self.assertIsNone(services.open_entry(self.divya))

    # --- UT_21_Att: duplicate check-in ------------------------------------------------------
    def test_ut_21_a_second_check_in_without_check_out_is_flagged(self):
        services.check_in(self.divya, self.warden)
        messages = self.errors(services.check_in, self.divya, self.warden)
        self.assertEqual(len(messages), 1)
        self.assertIn('already checked in since', messages[0])
        self.assertEqual(AttendanceRecord.objects.filter(student=self.divya).count(), 1)

    def test_an_open_check_in_from_an_earlier_day_also_blocks_a_new_one(self):
        services.check_in(self.divya, self.warden, at(2, 20))
        self.assertIn('already checked in since', self.errors(services.check_in, self.divya, self.warden)[0])
        self.assertEqual(AttendanceRecord.objects.filter(student=self.divya).count(), 1)

    def test_a_second_check_in_on_a_finished_day_is_refused(self):
        services.check_in(self.arjun, self.warden, at(1, 8))
        services.check_out(self.arjun, self.warden, at(1, 10))
        self.assertIn('is already complete', self.errors(services.check_in, self.arjun, self.warden, at(1, 18))[0])
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    # --- FR-07.04, ST_14_Att: check-out without a check-in -----------------------------------
    def test_st_14_check_out_without_a_check_in_is_an_error(self):
        self.assertEqual(self.errors(services.check_out, self.arjun, self.warden), ['No active check-in exists'])
        self.assertFalse(AttendanceRecord.objects.exists())

    def test_checking_out_twice_says_already_checked_out(self):
        services.check_in(self.arjun, self.warden)
        services.check_out(self.arjun, self.warden)
        self.assertEqual(self.errors(services.check_out, self.arjun, self.warden), ['Already checked out'])

    def test_check_out_cannot_be_before_the_check_in(self):
        services.check_in(self.arjun, self.warden, at(1, 20))
        messages = self.errors(services.check_out, self.arjun, self.warden, at(1, 19))
        self.assertIn('Check-out time cannot be before the check-in time', messages[0])
        self.assertIsNone(AttendanceRecord.objects.get().check_out_at)

    def test_a_check_out_time_in_the_future_is_refused(self):
        services.check_in(self.arjun, self.warden, at(1, 20))
        self.assertEqual(self.errors(services.check_out, self.arjun, self.warden, timezone.now() + timedelta(days=1)),
                         ['Time cannot be in the future'])

    # --- IT_20_Att: bulk marking -------------------------------------------------------------
    def test_it_20_bulk_check_in_records_every_selected_student_at_the_same_time(self):
        students = [self.new_student(f'bulk{i}') for i in range(10)]
        result = services.bulk_mark(students, 'check_in', self.warden, at(1, 20))
        self.assertEqual((len(result.done), result.failed), (10, []))
        self.assertEqual({r.check_in_at for r in result.done}, {at(1, 20)})
        self.assertEqual(AttendanceRecord.objects.filter(student__in=students).count(), 10)

    def test_bulk_marking_reports_each_failure_and_still_marks_the_rest(self):
        ok, already, no_room = self.new_student('ok'), self.new_student('already'), self.new_student('noroom', room=False)
        services.check_in(already, self.warden, at(1, 18))
        result = services.bulk_mark([ok, already, no_room], 'check_in', self.warden, at(1, 20))
        self.assertEqual([r.student for r in result.done], [ok])
        failed = {s.roll_no: text for s, text in result.failed}
        self.assertIn('already checked in since', failed['R-already'])
        self.assertIn('allocated room', failed['R-noroom'])

    def test_bulk_check_out(self):
        a, b = self.new_student('a'), self.new_student('b')
        services.bulk_mark([a, b], 'check_in', self.warden, at(1, 8))
        result = services.bulk_mark([a, b], 'check_out', self.warden, at(1, 17))
        self.assertEqual(len(result.done), 2)
        self.assertEqual(AttendanceRecord.objects.filter(check_out_at=at(1, 17)).count(), 2)

    def test_bulk_marking_needs_students_and_a_valid_action(self):
        self.assertEqual(self.errors(services.bulk_mark, [], 'check_in', self.warden), ['Select at least one student'])
        self.assertEqual(self.errors(services.bulk_mark, [self.arjun], 'delete', self.warden),
                         ['Action is not a valid choice'])

    # --- IT_19_Att: daily summary ------------------------------------------------------------
    def test_it_19_the_daily_summary_lists_present_and_absent_students(self):
        third = self.new_student('third')
        services.check_in(self.arjun, self.warden, at(1, 20))
        services.check_in(self.divya, self.warden, at(1, 19))
        services.check_out(self.divya, self.warden, at(1, 21))
        summary = services.daily_summary(self.warden, timezone.localdate() - timedelta(days=1))
        rows = {r['student'].roll_no: r for r in summary['rows']}
        self.assertEqual((rows['CSE2201']['status'], rows['CSE2202']['status'], rows['R-third']['status']),
                         ('inside', 'checked_out', 'absent'))
        self.assertEqual((summary['present'], summary['absent'], summary['total']), (2, 1, 3))
        self.assertEqual(rows['CSE2202']['duration'], '2 h 00 min')
        self.assertEqual(rows['CSE2201']['room'], 'A-101')
        self.assertTrue(rows['R-third']['can_check_in'])
        self.assertFalse(rows['CSE2201']['can_check_in'])
        self.assertTrue(rows['CSE2201']['can_check_out'])
        self.assertIsNotNone(third.pk)

    def test_a_student_without_a_room_is_not_listed_unless_they_were_recorded(self):
        loose = self.new_student('loose', room=False)
        summary = services.daily_summary(self.warden)
        self.assertNotIn(loose.pk, [r['student'].pk for r in summary['rows']])
        services.check_in(self.arjun, self.warden, at(1, 20))
        Allocation.objects.filter(student=self.arjun).update(status='ended', ended_on=date(2026, 10, 1))
        yesterday = services.daily_summary(self.warden, timezone.localdate() - timedelta(days=1))
        self.assertIn(self.arjun.pk, [r['student'].pk for r in yesterday['rows']])

    def test_an_open_entry_from_an_earlier_day_is_flagged_and_can_be_closed(self):
        services.check_in(self.arjun, self.warden, at(2, 20))
        flags = services.open_flags(self.warden)
        self.assertEqual([f.student for f in flags], [self.arjun])
        row = next(r for r in services.daily_summary(self.warden)['rows'] if r['student'] == self.arjun)
        self.assertTrue(row['open_from_earlier'])
        self.assertTrue(row['can_check_out'])
        self.assertFalse(row['can_check_in'])
        services.check_out(self.arjun, self.warden, at(1, 9))
        self.assertEqual(services.open_flags(self.warden), [])

    def test_todays_open_entry_is_not_flagged(self):
        services.check_in(self.arjun, self.warden)
        self.assertEqual(services.open_flags(self.warden), [])

    # --- IT_21_Att: history -------------------------------------------------------------------
    def test_it_21_history_only_contains_that_students_entries(self):
        services.check_in(self.arjun, self.warden, at(2, 20))
        services.check_out(self.arjun, self.warden, at(2, 22))
        services.check_in(self.divya, self.warden, at(1, 20))
        self.assertEqual([r.student for r in services.student_history(self.arjun)], [self.arjun])
        self.assertEqual([r.student for r in services.student_history(self.divya)], [self.divya])

    def test_history_is_newest_first_and_can_be_limited_by_date(self):
        for days in (4, 3, 2):
            services.check_in(self.arjun, self.warden, at(days, 8))
            services.check_out(self.arjun, self.warden, at(days, 17))
        dates = [r.attendance_date for r in services.student_history(self.arjun)]
        self.assertEqual(dates, sorted(dates, reverse=True))
        window = services.student_history(self.arjun, timezone.localdate() - timedelta(days=3),
                                          timezone.localdate() - timedelta(days=2))
        self.assertEqual(window.count(), 2)

    # --- ST_13_Att: report by date range --------------------------------------------------------
    def test_st_13_the_report_only_contains_entries_inside_the_range(self):
        today = timezone.localdate()
        for days in (10, 5, 2):
            services.check_in(self.arjun, self.warden, at(days, 8))
            services.check_out(self.arjun, self.warden, at(days, 17))
        services.check_in(self.arjun, self.warden)                        # today, at the current time
        services.check_in(self.divya, self.warden, at(3, 8))
        report = services.attendance_report(self.warden, today - timedelta(days=7), today)
        self.assertEqual(sorted(r.attendance_date for r in report['rows']),
                         sorted([today - timedelta(days=5), today - timedelta(days=3),
                                 today - timedelta(days=2), today]))
        self.assertEqual({e['student'].roll_no: e['days'] for e in report['per_student']},
                         {'CSE2201': 3, 'CSE2202': 1})
        self.assertEqual(report['total'], 4)
        only = services.attendance_report(self.warden, today - timedelta(days=7), today, self.divya)
        self.assertEqual([r.student for r in only['rows']], [self.divya])

    def test_the_report_shows_the_duration_of_each_entry(self):
        services.check_in(self.arjun, self.warden, at(1, 8))
        services.check_out(self.arjun, self.warden, at(1, 17, 30))
        day = timezone.localdate() - timedelta(days=1)
        self.assertEqual(services.attendance_report(self.warden, day, day)['rows'][0].duration, '9 h 30 min')

    def test_the_report_range_must_be_in_order(self):
        today = timezone.localdate()
        self.assertEqual(self.errors(services.attendance_report, self.warden, today, today - timedelta(days=1)),
                         ['End date cannot be before Start date'])

    def test_staff_only_see_students_of_their_own_hostel(self):
        other = Hostel.objects.create(name='North Hostel', code='NORTH')
        outsider = self.new_student('north', hostel=other)
        services.check_in(self.arjun, self.warden, at(1, 20))
        services.check_in(outsider, self.warden, at(1, 20))
        self.warden.hostel = self.arjun.hostel
        day = timezone.localdate() - timedelta(days=1)
        self.assertEqual([r['student'] for r in services.daily_summary(self.warden, day)['rows']],
                         [self.arjun, self.divya])
        self.assertEqual([r.student for r in services.attendance_report(self.warden, day, day)['rows']], [self.arjun])
        self.warden.hostel = other
        self.assertEqual([r['student'] for r in services.daily_summary(self.warden, day)['rows']], [outsider])
        self.warden.hostel = None
        self.assertEqual(len(services.attendance_report(self.warden, day, day)['rows']), 2)

    # --- helpers ---------------------------------------------------------------------------------
    def test_durations_and_times_are_formatted_for_people(self):
        self.assertEqual(services.format_duration(at(1, 8), at(1, 8, 5)), '0 h 05 min')
        self.assertEqual(services.format_duration(at(1, 20), at(0, 9, 30)), '13 h 30 min')
        self.assertEqual(services.format_duration(at(1, 8), None), '')
        self.assertEqual(services.format_time(None), '')
        self.assertEqual(services.format_time(at(1, 20))[-8:], '08:00 PM')
