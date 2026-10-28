"""FR-07 screens: marking, bulk marking, daily summary, history, report, My Attendance."""
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Allocation, AttendanceRecord, Hostel, Room, Student, UserAccount
from core.navigation import build_menu
from core.seed import seed

from . import services


def at(days_ago, hour, minute=0):
    day = timezone.localdate() - timedelta(days=days_ago)
    return timezone.make_aware(datetime(day.year, day.month, day.day, hour, minute))


def form_time(days_ago, hour, minute=0):
    """The value of a datetime-local input, e.g. 2026-10-27T20:00."""
    return at(days_ago, hour, minute).strftime('%Y-%m-%dT%H:%M')


class AttendanceViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.room = Room.objects.get(room_no='A-101')
        for student in (cls.arjun, cls.divya):
            Allocation.objects.create(student=student, room=cls.room, allocated_on=date(2026, 7, 1))

    def login(self, username):
        self.client.force_login(get_user_model().objects.get(username=username))

    def shown(self, response):
        return [str(m) for m in response.context['messages']]

    def new_student(self, name, room=True):
        user = get_user_model().objects.create(username=f'user_{name}')
        account = UserAccount.objects.create(user=user, role='student', hostel=self.arjun.hostel)
        student = Student.objects.create(user_account=account, hostel=self.arjun.hostel,
                                         roll_no=f'R-{name}', full_name=name.title())
        if room:
            Allocation.objects.create(student=student, room=self.room, allocated_on=date(2026, 7, 1))
        return student

    def post(self, name, data, follow=True):
        return self.client.post(reverse(f'attendance:{name}'), data, follow=follow)

    # --- access ------------------------------------------------------------------------------
    def test_visitors_must_log_in(self):
        for url in (reverse('attendance:my_attendance'), reverse('attendance:manage'), reverse('attendance:report'),
                    reverse('attendance:student_history', args=[self.arjun.pk])):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn('/login/', response['Location'])

    def test_students_cannot_use_the_staff_screens(self):
        self.login('stu1023')
        for url in (reverse('attendance:manage'), reverse('attendance:report'),
                    reverse('attendance:student_history', args=[self.divya.pk])):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        for name in ('check_in', 'check_out', 'bulk'):
            self.assertEqual(self.post(name, {'student': self.arjun.pk}, follow=False).status_code, 403, name)
        self.assertFalse(AttendanceRecord.objects.exists())

    def test_wardens_and_the_administrator_can_open_the_staff_screens(self):
        for username in ('wdn05', 'admin01'):
            self.login(username)
            for url in (reverse('attendance:manage'), reverse('attendance:report'),
                        reverse('attendance:student_history', args=[self.arjun.pk])):
                self.assertEqual(self.client.get(url).status_code, 200, (username, url))
        self.assertEqual(self.client.get(reverse('attendance:my_attendance')).status_code, 403)

    def test_marking_must_be_posted(self):
        self.login('wdn05')
        for name in ('check_in', 'check_out', 'bulk'):
            self.assertEqual(self.client.get(reverse(f'attendance:{name}')).status_code, 405, name)

    def test_menu_links_work_for_every_role(self):
        for role, url_name in (('student', 'attendance:my_attendance'), ('warden', 'attendance:manage'),
                               ('admin', 'attendance:manage')):
            item = next(i for i in build_menu(role) if i['label'] == 'Attendance')
            self.assertEqual(item['url'], reverse(url_name), role)

    # --- UT_19_Att, UT_20_Att: single check-in and check-out ----------------------------------
    def test_ut_19_warden_checks_a_student_in(self):
        self.login('wdn05')
        response = self.post('check_in', {'student': self.divya.pk, 'when': form_time(1, 20)})
        record = AttendanceRecord.objects.get()
        self.assertEqual((record.student, record.check_in_at, record.recorded_by), (self.divya, at(1, 20), self.warden))
        self.assertIn('Divya S. checked in', self.shown(response))

    def test_checking_in_without_a_time_uses_now(self):
        self.login('wdn05')
        self.post('check_in', {'student': self.arjun.pk})
        self.assertLess(abs((timezone.now() - AttendanceRecord.objects.get().check_in_at).total_seconds()), 30)

    def test_ut_20_warden_checks_a_student_out_the_next_morning(self):
        self.login('wdn05')
        self.post('check_in', {'student': self.divya.pk, 'when': form_time(3, 20)})
        response = self.post('check_out', {'student': self.divya.pk, 'when': form_time(2, 9, 30)})
        record = AttendanceRecord.objects.get()
        self.assertEqual(record.check_out_at, at(2, 9, 30))
        self.assertIn('Divya S. checked out', self.shown(response))

    def test_the_page_after_marking_stays_on_the_chosen_day(self):
        self.login('wdn05')
        day = (timezone.localdate() - timedelta(days=1)).isoformat()
        response = self.post('check_in', {'student': self.arjun.pk, 'when': form_time(1, 20), 'date': day})
        self.assertEqual(response.redirect_chain[-1][0], f"{reverse('attendance:manage')}?date={day}")

    # --- UT_21_Att, ST_14_Att, FR-07.05: errors are shown ---------------------------------------
    def test_ut_21_duplicate_check_in_is_flagged_and_not_saved(self):
        self.login('wdn05')
        self.post('check_in', {'student': self.arjun.pk, 'when': form_time(1, 20)})
        response = self.post('check_in', {'student': self.arjun.pk, 'when': form_time(1, 21)})
        self.assertTrue(any('already checked in since' in m for m in self.shown(response)))
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_st_14_check_out_without_a_check_in_shows_an_error(self):
        self.login('wdn05')
        response = self.post('check_out', {'student': self.arjun.pk})
        self.assertIn('No active check-in exists', self.shown(response))
        self.assertFalse(AttendanceRecord.objects.exists())

    def test_a_student_without_a_room_is_refused_on_screen(self):
        loose = self.new_student('loose', room=False)
        self.login('wdn05')
        response = self.post('check_in', {'student': loose.pk})
        self.assertIn('Attendance can only be recorded for students with an allocated room', self.shown(response))

    def test_a_bad_or_future_time_shows_an_error(self):
        self.login('wdn05')
        response = self.post('check_in', {'student': self.arjun.pk, 'when': 'tomorrow evening'})
        self.assertIn('Time format is invalid', self.shown(response))
        future = (timezone.localtime() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        response = self.post('check_in', {'student': self.arjun.pk, 'when': future})
        self.assertIn('Time cannot be in the future', self.shown(response))
        self.assertFalse(AttendanceRecord.objects.exists())

    def test_an_unknown_student_is_a_404(self):
        self.login('wdn05')
        self.assertEqual(self.post('check_in', {'student': 99999}, follow=False).status_code, 404)

    # --- IT_20_Att: bulk ----------------------------------------------------------------------------
    def test_it_20_bulk_check_in_marks_all_selected_students(self):
        students = [self.new_student(f'bulk{i}') for i in range(10)]
        self.login('wdn05')
        response = self.post('bulk', {'students': [s.pk for s in students], 'action': 'check_in',
                                      'when': form_time(1, 20)})
        self.assertIn('10 student(s) checked in', self.shown(response))
        self.assertEqual({r.check_in_at for r in AttendanceRecord.objects.filter(student__in=students)}, {at(1, 20)})

    def test_bulk_marking_shows_a_message_per_failed_student(self):
        ok, again = self.new_student('ok'), self.new_student('again')
        self.login('wdn05')
        self.post('check_in', {'student': again.pk, 'when': form_time(1, 18)})
        response = self.post('bulk', {'students': [ok.pk, again.pk], 'action': 'check_in', 'when': form_time(1, 20)})
        messages = self.shown(response)
        self.assertIn('1 student(s) checked in', messages)
        self.assertTrue(any(m.startswith('Again: Student is already checked in since') for m in messages))

    def test_bulk_marking_without_a_selection_shows_an_error(self):
        self.login('wdn05')
        response = self.post('bulk', {'action': 'check_in'})
        self.assertIn('Select at least one student', self.shown(response))

    # --- IT_19_Att: the daily page ------------------------------------------------------------------
    def test_it_19_the_daily_page_shows_present_and_absent(self):
        third = self.new_student('third')
        self.login('wdn05')
        self.post('check_in', {'student': self.arjun.pk, 'when': form_time(1, 20)})
        self.post('check_in', {'student': self.divya.pk, 'when': form_time(1, 19)})
        self.post('check_out', {'student': self.divya.pk, 'when': form_time(1, 21)})
        day = (timezone.localdate() - timedelta(days=1)).isoformat()
        response = self.client.get(reverse('attendance:manage'), {'date': day})
        summary = response.context['summary']
        self.assertEqual((summary['present'], summary['absent'], summary['total']), (2, 1, 3))
        self.assertContains(response, 'Present, checked in')
        self.assertContains(response, 'Present, checked out')
        self.assertContains(response, 'Absent')
        self.assertContains(response, third.full_name)

    def test_an_invalid_date_falls_back_to_today(self):
        self.login('wdn05')
        response = self.client.get(reverse('attendance:manage'), {'date': 'garbage'})
        self.assertEqual(response.context['summary']['day'], timezone.localdate())

    def test_the_daily_page_warns_about_check_ins_that_were_never_closed(self):
        self.login('wdn05')
        self.post('check_in', {'student': self.arjun.pk, 'when': form_time(2, 20)})
        response = self.client.get(reverse('attendance:manage'))
        self.assertContains(response, 'check-in')
        self.assertContains(response, 'never closed')
        self.assertContains(response, 'Open since')

    def test_the_daily_page_explains_when_nobody_has_a_room(self):
        Allocation.objects.all().update(status='ended', ended_on=date(2026, 10, 1))
        self.login('wdn05')
        response = self.client.get(reverse('attendance:manage'))
        self.assertContains(response, 'No students have a room yet')

    # --- IT_21_Att, FR-07.08: history ----------------------------------------------------------------
    def test_it_21_a_student_sees_only_their_own_entries(self):
        services.check_in(self.arjun, self.warden, at(2, 20))
        services.check_in(self.divya, self.warden, at(1, 21, 15))
        self.login('stu1023')
        response = self.client.get(reverse('attendance:my_attendance'))
        self.assertEqual([r.student for r in response.context['records']], [self.arjun])
        self.assertContains(response, 'My Attendance')
        self.assertContains(response, 'Not checked out')

    def test_it_21_the_staff_history_page_is_for_one_student(self):
        services.check_in(self.arjun, self.warden, at(2, 20))
        services.check_out(self.arjun, self.warden, at(2, 22, 30))
        services.check_in(self.divya, self.warden, at(1, 21))
        self.login('wdn05')
        response = self.client.get(reverse('attendance:student_history', args=[self.arjun.pk]))
        self.assertEqual([r.student for r in response.context['records']], [self.arjun])
        self.assertContains(response, 'Arjun Rao')
        self.assertContains(response, '2 h 30 min')

    def test_a_student_with_no_entries_sees_a_friendly_message(self):
        self.login('stu1023')
        self.assertContains(self.client.get(reverse('attendance:my_attendance')), 'No attendance has been recorded yet')

    def test_a_user_without_a_student_record_sees_a_friendly_message(self):
        user = get_user_model().objects.create_user(username='lonely', password='x')
        UserAccount.objects.create(user=user, role='student')
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse('attendance:my_attendance')),
                            'student record has not been created yet')

    def test_the_history_can_be_shown_on_any_page_with_the_template_tag(self):
        services.check_in(self.arjun, self.warden, at(2, 20))
        services.check_in(self.divya, self.warden, at(1, 20))
        html = Template('{% load attendance_tags %}{% attendance_history student %}').render(Context({'student': self.arjun}))
        self.assertIn('Not checked out', html)
        self.assertEqual(html.count('<tr>'), 2)                  # header row + Arjun's one entry
        self.assertIn('No attendance has been recorded yet',
                      Template('{% load attendance_tags %}{% attendance_history student %}').render(
                          Context({'student': self.new_student('empty')})))

    # --- ST_13_Att: report ------------------------------------------------------------------------------
    def test_st_13_the_report_defaults_to_the_last_seven_days(self):
        services.check_in(self.arjun, self.warden, at(20, 8))
        services.check_in(self.divya, self.warden, at(3, 8))
        self.login('wdn05')
        response = self.client.get(reverse('attendance:report'))
        self.assertEqual([r.student for r in response.context['result']['rows']], [self.divya])

    def test_st_13_the_report_can_use_any_range_and_student(self):
        services.check_in(self.arjun, self.warden, at(20, 8))
        services.check_in(self.divya, self.warden, at(3, 8))
        self.login('wdn05')
        today = timezone.localdate()
        params = {'start': (today - timedelta(days=30)).isoformat(), 'end': today.isoformat()}
        self.assertEqual(self.client.get(reverse('attendance:report'), params).context['result']['total'], 2)
        params['student'] = self.arjun.pk
        response = self.client.get(reverse('attendance:report'), params)
        self.assertEqual([r.student for r in response.context['result']['rows']], [self.arjun])

    def test_the_report_checks_its_dates(self):
        self.login('wdn05')
        today = timezone.localdate()
        response = self.client.get(reverse('attendance:report'),
                                   {'start': today.isoformat(), 'end': (today - timedelta(days=2)).isoformat()})
        self.assertIn('End date cannot be before Start date', self.shown(response))
        response = self.client.get(reverse('attendance:report'), {'start': 'nope'})
        self.assertIn('Date format is invalid', self.shown(response))

    def test_an_empty_report_says_so(self):
        self.login('wdn05')
        self.assertContains(self.client.get(reverse('attendance:report')), 'No attendance was recorded between')

    def test_the_report_can_be_downloaded_as_csv_and_is_safe_for_spreadsheets(self):
        evil = self.new_student('evil')
        Student.objects.filter(pk=evil.pk).update(full_name='=HYPERLINK("http://bad")')
        services.check_in(evil, self.warden, at(1, 8))
        services.check_out(evil, self.warden, at(1, 17))
        self.login('wdn05')
        response = self.client.get(reverse('attendance:report'), {'export': 'csv'})
        self.assertEqual(response['Content-Type'], 'text/csv')
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], 'Date,Roll no,Student,Check-in,Check-out,Duration')
        self.assertIn("'=HYPERLINK", lines[1])
        self.assertTrue(lines[1].endswith('9 h 00 min'))

    # --- hostel scope --------------------------------------------------------------------------------------
    def test_a_warden_cannot_mark_a_student_from_another_hostel(self):
        other = Hostel.objects.create(name='North Hostel', code='NORTH')
        outsider = self.new_student('north')
        Student.objects.filter(pk=outsider.pk).update(hostel=other)
        self.warden.hostel = self.arjun.hostel
        self.warden.save()
        self.login('wdn05')
        self.assertEqual(self.post('check_in', {'student': outsider.pk}, follow=False).status_code, 404)
        self.assertEqual(self.client.get(reverse('attendance:student_history', args=[outsider.pk])).status_code, 404)
