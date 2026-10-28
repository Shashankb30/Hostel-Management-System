"""FR-06 rules: submit, misconduct and demerit points, status, reopen, escalation, summary."""
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import Complaint, DemeritRecord, DemeritRule, Hostel, Notification, Student, UserAccount
from core.seed import seed

from . import services


class ComplaintServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')

    def complain(self, student=None, category='maintenance', description='Fan not working'):
        return services.submit_complaint(student or self.arjun, category, description)

    def misconduct(self, severity='moderate', student=None, description='Loud music after 11 pm'):
        return services.log_misconduct(student or self.arjun, severity, description, self.warden)

    def errors(self, call, *args, **kwargs):
        with self.assertRaises(ValidationError) as caught:
            call(*args, **kwargs)
        return caught.exception.messages

    # --- UT_16_Comp, UT_17_Comp: submit and validate -----------------------------------------
    def test_ut_16_submitted_complaint_is_open_with_a_unique_id(self):
        first, second = self.complain(), self.complain(description='Tap leaking')
        self.assertEqual(first.status, 'open')
        self.assertEqual(first.kind, 'complaint')
        self.assertEqual(first.student, self.arjun)
        self.assertEqual(first.hostel, self.arjun.hostel)
        self.assertRegex(first.complaint_id, r'^CMP\d{5}$')
        self.assertNotEqual(first.complaint_id, second.complaint_id)
        self.assertEqual(first.title, 'Fan not working')
        self.assertEqual(first.updates.get().new_status, 'open')

    def test_a_subject_can_be_given_and_is_trimmed(self):
        c = services.submit_complaint(self.arjun, 'food', '  Mess food was cold  ', '  Cold food ')
        self.assertEqual((c.title, c.description), ('Cold food', 'Mess food was cold'))

    def test_ut_17_blank_description_is_rejected(self):
        for blank in ('', '   ', None):
            self.assertEqual(self.errors(services.submit_complaint, self.arjun, 'maintenance', blank),
                             ['Description is required'])
        self.assertFalse(Complaint.objects.exists())

    def test_category_is_required_and_must_be_valid(self):
        self.assertEqual(self.errors(services.submit_complaint, self.arjun, '', 'x'), ['Category is required'])
        self.assertEqual(self.errors(services.submit_complaint, self.arjun, 'noise', 'x'),
                         ['Category is not a valid choice'])

    def test_every_error_is_reported_together(self):
        messages = self.errors(services.submit_complaint, self.arjun, '', '')
        self.assertCountEqual(messages, ['Category is required', 'Description is required'])

    def test_overlong_text_is_rejected(self):
        self.assertEqual(self.errors(services.submit_complaint, self.arjun, 'other', 'x' * 2001),
                         ['Description must be at most 2000 characters'])
        self.assertEqual(self.errors(services.submit_complaint, self.arjun, 'other', 'x', 'y' * 161),
                         ['Title must be at most 160 characters'])

    # --- IT_16_Comp, IT_18_Comp: misconduct and demerit points --------------------------------
    def test_default_rules_exist(self):
        self.assertEqual({r.severity: r.points for r in services.list_rules()},
                         {'minor': 1, 'moderate': 3, 'major': 5})

    def new_student(self, name):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create(username=f'user_{name}')
        account = UserAccount.objects.create(user=user, role='student', hostel=self.arjun.hostel)
        return Student.objects.create(user_account=account, hostel=self.arjun.hostel,
                                      roll_no=f'R-{name}', full_name=name.title())

    def test_it_16_points_follow_the_severity_rule(self):
        for severity, points in (('minor', 1), ('moderate', 3), ('major', 5)):
            student = self.new_student(severity)
            case = self.misconduct(severity, student=student)
            self.assertEqual(case.demerit_records.get().points, points)
            self.assertEqual(case.kind, 'misconduct')
            self.assertEqual(case.severity, severity)
            self.assertEqual(services.demerit_total(student), points)

    def test_it_18_points_accumulate_across_cases(self):
        DemeritRecord.objects.create(student=self.arjun, points=2, reason='Earlier case',
                                     awarded_by=self.warden, awarded_on='2026-10-01')
        self.assertEqual(services.demerit_total(self.arjun), 2)
        self.misconduct('moderate')                       # 3 points
        self.assertEqual(services.demerit_total(self.arjun), 5)
        self.assertEqual(services.demerit_total(self.divya), 0)

    def test_points_are_only_for_the_student_the_case_is_about(self):
        self.misconduct('major', student=self.divya)
        self.assertEqual(services.demerit_total(self.divya), 5)
        self.assertEqual(services.demerit_total(self.arjun), 0)

    def test_severity_and_description_are_required_for_misconduct(self):
        self.assertEqual(self.errors(services.log_misconduct, self.arjun, '', 'x', self.warden),
                         ['Severity is required'])
        self.assertEqual(self.errors(services.log_misconduct, self.arjun, 'severe', 'x', self.warden),
                         ['Severity is not a valid choice'])
        self.assertEqual(self.errors(services.log_misconduct, self.arjun, 'minor', ' ', self.warden),
                         ['Description is required'])
        self.assertFalse(Complaint.objects.exists())
        self.assertFalse(DemeritRecord.objects.exists())

    def test_the_student_is_notified_of_a_misconduct_case_with_their_total(self):
        self.misconduct('moderate')
        note = Notification.objects.get(recipient=self.arjun.user_account, category='COMPLAINT')
        self.assertIn('3 demerit point(s)', note.message)
        self.assertIn('total is 3', note.message)

    def test_a_zero_point_rule_adds_no_demerit_record(self):
        services.update_rules({'minor': 0})
        self.misconduct('minor')
        self.assertFalse(DemeritRecord.objects.exists())

    # --- rules (FR-06.05) -------------------------------------------------------------------
    def test_changing_a_rule_does_not_rewrite_old_records(self):
        old = self.misconduct('moderate')
        services.update_rules({'moderate': 4})
        new = self.misconduct('moderate', description='Second case')
        self.assertEqual(old.demerit_records.get().points, 3)
        self.assertEqual(new.demerit_records.get().points, 4)
        self.assertEqual(services.demerit_total(self.arjun), 7)

    def test_rule_points_are_validated(self):
        self.assertEqual(self.errors(services.update_rules, {'minor': ''}), ['Minor points is required'])
        self.assertEqual(self.errors(services.update_rules, {'minor': 'abc'}), ['Minor points must be a whole number'])
        self.assertEqual(self.errors(services.update_rules, {'minor': '-1'}), ['Minor points must be at least 0'])
        self.assertEqual(self.errors(services.update_rules, {'minor': '101'}), ['Minor points must be at most 100'])
        self.assertEqual(DemeritRule.objects.get(severity='minor').points, 1)

    def test_nothing_is_saved_if_any_rule_is_invalid(self):
        self.errors(services.update_rules, {'minor': '2', 'major': 'oops'})
        self.assertEqual(DemeritRule.objects.get(severity='minor').points, 1)

    # --- IT_17_Comp: status, remarks, notification ------------------------------------------
    def test_it_17_resolving_updates_the_status_and_notifies_the_student(self):
        c = self.complain()
        services.change_status(c, 'resolved', 'Fan replaced', self.warden)
        c.refresh_from_db()
        self.assertEqual((c.status, c.remarks), ('resolved', 'Fan replaced'))
        self.assertEqual(c.resolved_by, self.warden)
        self.assertIsNotNone(c.resolved_at)
        note = Notification.objects.get(recipient=self.arjun.user_account, category='COMPLAINT')
        self.assertIn(c.complaint_id, note.message)
        self.assertIn('Resolved', note.message)
        self.assertIn('Fan replaced', note.message)
        self.assertFalse(note.is_read)

    def test_resolving_needs_remarks_but_review_does_not(self):
        c = self.complain()
        self.assertEqual(self.errors(services.change_status, c, 'resolved', '  ', self.warden),
                         ['Remarks is required'])
        services.change_status(c, 'under_review', '', self.warden)
        c.refresh_from_db()
        self.assertEqual(c.status, 'under_review')

    def test_every_status_change_is_kept_in_the_history(self):
        c = self.complain()
        services.change_status(c, 'under_review', 'Looking into it', self.warden)
        services.change_status(c, 'resolved', 'Fixed', self.warden)
        history = [(u.old_status, u.new_status, u.remarks) for u in c.updates.all()]
        self.assertEqual(history, [('', 'open', 'Complaint submitted'),
                                   ('open', 'under_review', 'Looking into it'),
                                   ('under_review', 'resolved', 'Fixed')])

    def test_invalid_status_changes_are_refused(self):
        c = self.complain()
        self.assertEqual(self.errors(services.change_status, c, 'open', 'x', self.warden),
                         ['A complaint cannot move from Open to Open'])
        self.assertEqual(self.errors(services.change_status, c, 'closed', 'x', self.warden),
                         ['Status is not a valid choice'])
        self.assertEqual(self.errors(services.change_status, c, '', 'x', self.warden), ['Status is required'])

    def test_a_resolved_complaint_cannot_be_moved_without_reopening(self):
        c = self.complain()
        services.change_status(c, 'resolved', 'Done', self.warden)
        self.assertEqual(self.errors(services.change_status, c, 'open', 'again', self.warden),
                         ['A resolved complaint cannot be edited; reopen it first'])

    # --- ST_12_Comp: resolved complaints are locked -----------------------------------------
    def test_st_12_a_resolved_complaint_cannot_be_edited(self):
        c = self.complain()
        services.change_status(c, 'resolved', 'Done', self.warden)
        self.assertEqual(self.errors(services.edit_complaint, c, 'New text'),
                         ['A resolved complaint cannot be edited; reopen it first'])
        c.refresh_from_db()
        self.assertEqual(c.description, 'Fan not working')

    def test_st_12_after_reopening_the_complaint_can_be_edited_again(self):
        c = self.complain()
        services.change_status(c, 'resolved', 'Done', self.warden)
        services.reopen(c, 'Still broken', self.warden)
        c.refresh_from_db()
        self.assertEqual((c.status, c.resolved_at, c.resolved_by), ('open', None, None))
        services.edit_complaint(c, 'Fan still not working', 'maintenance')
        c.refresh_from_db()
        self.assertEqual(c.description, 'Fan still not working')
        self.assertIn('reopened', Notification.objects.filter(recipient=self.arjun.user_account).first().message)

    def test_only_a_resolved_complaint_can_be_reopened_and_remarks_are_needed(self):
        c = self.complain()
        self.assertEqual(self.errors(services.reopen, c, 'why', self.warden),
                         ['Only a resolved complaint can be reopened'])
        services.change_status(c, 'resolved', 'Done', self.warden)
        self.assertEqual(self.errors(services.reopen, c, ' ', self.warden), ['Remarks is required'])

    def test_editing_still_validates_the_text(self):
        c = self.complain()
        self.assertEqual(self.errors(services.edit_complaint, c, ' '), ['Description is required'])

    # --- FR-06.10: escalation ---------------------------------------------------------------
    def test_a_major_case_is_escalated_and_the_administrator_is_told(self):
        case = self.misconduct('major')
        case.refresh_from_db()
        self.assertTrue(case.is_escalated)
        self.assertIn('Major misconduct', case.escalation_reason)
        note = Notification.objects.get(recipient=self.admin, category='COMPLAINT')
        self.assertIn(case.complaint_id, note.message)

    def test_a_minor_case_is_not_escalated(self):
        case = self.misconduct('minor')
        case.refresh_from_db()
        self.assertFalse(case.is_escalated)
        self.assertFalse(Notification.objects.filter(recipient=self.admin).exists())

    def test_repeated_misconduct_is_escalated_on_the_third_case(self):
        first, second = self.misconduct('minor'), self.misconduct('minor')
        third = self.misconduct('minor')
        for case in (first, second, third):
            case.refresh_from_db()
        self.assertEqual([first.is_escalated, second.is_escalated, third.is_escalated], [False, False, True])
        self.assertIn('Repeated misconduct (3 cases)', third.escalation_reason)

    def test_reaching_the_point_limit_is_escalated(self):
        services.update_rules({'minor': 5})
        first = self.misconduct('minor')               # 5 points, one case: no escalation
        first.refresh_from_db()
        self.assertFalse(first.is_escalated)
        second = self.misconduct('minor')              # 10 points
        second.refresh_from_db()
        self.assertTrue(second.is_escalated)
        self.assertEqual(second.escalation_reason, 'Demerit total reached 10')

    def test_repeated_unresolved_complaints_in_one_category_are_escalated(self):
        a, b = self.complain(), self.complain(description='Light broken')
        c = self.complain(description='Window stuck')
        for x in (a, b, c):
            x.refresh_from_db()
        self.assertEqual([a.is_escalated, b.is_escalated, c.is_escalated], [False, False, True])
        self.assertIn('Repeated maintenance complaint', c.escalation_reason)

    def test_staff_can_escalate_by_hand_once(self):
        c = self.complain()
        services.escalate(c, 'Safety risk', self.warden)
        c.refresh_from_db()
        self.assertTrue(c.is_escalated)
        self.assertEqual(c.escalation_reason, 'Safety risk')
        self.assertEqual(self.errors(services.escalate, c, 'again', self.warden),
                         ['Complaint is already escalated to the administrator'])
        self.assertEqual(self.errors(services.escalate, self.complain(), ' ', self.warden), ['Reason is required'])

    # --- UT_18_Comp, FR-06.12: viewing -----------------------------------------------------
    def test_ut_18_staff_can_filter_by_status_category_and_type(self):
        open_one = self.complain()
        resolved = self.complain(student=self.divya, category='food', description='Cold food')
        services.change_status(resolved, 'resolved', 'Talked to the mess', self.warden)
        case = self.misconduct('minor')
        ids = lambda qs: {c.pk for c in qs}            # noqa: E731
        self.assertEqual(ids(services.list_complaints(self.warden)), {open_one.pk, resolved.pk, case.pk})
        self.assertEqual(ids(services.list_complaints(self.warden, status='open')), {open_one.pk, case.pk})
        self.assertEqual(ids(services.list_complaints(self.warden, status='resolved')), {resolved.pk})
        self.assertEqual(ids(services.list_complaints(self.warden, category='food')), {resolved.pk})
        self.assertEqual(ids(services.list_complaints(self.warden, kind='misconduct')), {case.pk})
        self.assertEqual(ids(services.list_complaints(self.warden, search='divya')), {resolved.pk})
        self.assertEqual(ids(services.list_complaints(self.warden, status='nonsense')),
                         {open_one.pk, resolved.pk, case.pk})

    def test_a_student_sees_their_own_complaints_but_not_misconduct_cases(self):
        mine, theirs = self.complain(), self.complain(student=self.divya)
        self.misconduct('minor')
        self.assertEqual(list(services.student_complaints(self.arjun)), [mine])
        self.assertEqual(list(services.student_complaints(self.divya)), [theirs])

    def test_staff_only_see_complaints_of_their_own_hostel(self):
        other = Hostel.objects.create(name='North Hostel', code='NORTH')
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create(username='north_student')
        outsider = Student.objects.create(
            user_account=UserAccount.objects.create(user=user, role='student', hostel=other),
            hostel=other, roll_no='N-1', full_name='North Student')
        mine, theirs = self.complain(), self.complain(student=outsider)
        self.warden.hostel = self.arjun.hostel
        self.assertEqual({c.pk for c in services.list_complaints(self.warden)}, {mine.pk})
        self.warden.hostel = other
        self.assertEqual({c.pk for c in services.list_complaints(self.warden)}, {theirs.pk})
        self.warden.hostel = None
        self.assertEqual({c.pk for c in services.list_complaints(self.warden)}, {mine.pk, theirs.pk})

    # --- ST_11_Comp: summary by category ---------------------------------------------------
    def test_st_11_summary_groups_complaints_by_category(self):
        self.complain(category='maintenance')
        self.complain(category='maintenance', description='Tap')
        done = self.complain(category='maintenance', description='Light')
        services.change_status(done, 'resolved', 'Fixed', self.warden)
        self.misconduct('minor')                                   # discipline
        self.complain(student=self.divya, category='food', description='Cold food')
        summary = services.category_summary(self.warden)
        rows = {r['category']: r for r in summary['rows']}
        self.assertEqual((rows['maintenance']['total'], rows['maintenance']['open'], rows['maintenance']['resolved']),
                         (3, 2, 1))
        self.assertEqual(rows['discipline']['total'], 1)
        self.assertEqual(rows['food']['total'], 1)
        self.assertEqual(rows['other']['total'], 0)
        self.assertEqual(summary['totals']['total'], 5)
        self.assertEqual([r['label'] for r in summary['rows']], ['Maintenance', 'Discipline', 'Food', 'Other'])

    def test_the_summary_can_be_limited_to_a_date_range(self):
        from datetime import date, timedelta
        self.complain()
        today = date.today()
        self.assertEqual(services.category_summary(self.warden, today, today)['totals']['total'], 1)
        self.assertEqual(services.category_summary(
            self.warden, today + timedelta(days=1), None)['totals']['total'], 0)
        self.assertEqual(services.category_summary(
            self.warden, None, today - timedelta(days=1))['totals']['total'], 0)
