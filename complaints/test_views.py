"""FR-06 screens: student complaints, warden and administrator case handling, rules, report."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Complaint, Notification, Student, UserAccount
from core.navigation import build_menu
from core.seed import seed

from . import services


class ComplaintViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')

    def login(self, username):
        self.client.force_login(get_user_model().objects.get(username=username))

    def shown(self, response):
        return [str(m) for m in response.context['messages']]

    def complain(self, student=None, category='maintenance', description='Fan not working'):
        return services.submit_complaint(student or self.arjun, category, description)

    # --- access ----------------------------------------------------------------------------
    def test_visitors_must_log_in(self):
        for name, args in (('my_complaints', []), ('manage', []), ('rules', []), ('report', []),
                           ('log_misconduct', [])):
            response = self.client.get(reverse(f'complaints:{name}', args=args))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn('/login/', response['Location'])

    def test_students_cannot_open_the_staff_screens(self):
        self.login('stu1023')
        for name in ('manage', 'rules', 'report', 'log_misconduct'):
            self.assertEqual(self.client.get(reverse(f'complaints:{name}')).status_code, 403, name)
        c = self.complain()
        for name in ('update_status', 'reopen', 'escalate'):
            self.assertEqual(self.client.post(reverse(f'complaints:{name}', args=[c.pk])).status_code, 403, name)

    def test_wardens_use_manage_but_not_the_student_page(self):
        self.login('wdn05')
        self.assertEqual(self.client.get(reverse('complaints:manage')).status_code, 200)
        self.assertEqual(self.client.get(reverse('complaints:my_complaints')).status_code, 403)

    def test_the_administrator_can_open_the_staff_screens(self):
        self.login('admin01')
        for name in ('manage', 'rules', 'report', 'log_misconduct'):
            self.assertEqual(self.client.get(reverse(f'complaints:{name}')).status_code, 200, name)

    def test_menu_links_work_for_every_role(self):
        for role, label, url_name in (('student', 'Complaints', 'complaints:my_complaints'),
                                      ('warden', 'Complaints', 'complaints:manage'),
                                      ('admin', 'Complaints', 'complaints:manage')):
            item = next(i for i in build_menu(role) if i['label'] == label)
            self.assertEqual(item['url'], reverse(url_name), role)

    # --- UT_16_Comp, UT_17_Comp: student submits --------------------------------------------
    def test_ut_16_student_submits_a_complaint(self):
        self.login('stu1023')
        response = self.client.post(reverse('complaints:my_complaints'),
                                    {'category': 'maintenance', 'description': 'Fan not working'}, follow=True)
        complaint = Complaint.objects.get()
        self.assertEqual((complaint.status, complaint.student, complaint.category),
                         ('open', self.arjun, 'maintenance'))
        self.assertIn(f'Complaint {complaint.complaint_id} submitted. Status: Open', self.shown(response))
        self.assertContains(response, 'Fan not working')
        self.assertContains(response, complaint.complaint_id)

    def test_ut_17_blank_description_shows_an_error_and_keeps_the_form(self):
        self.login('stu1023')
        response = self.client.post(reverse('complaints:my_complaints'),
                                    {'category': 'food', 'description': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Description is required', self.shown(response))
        self.assertFalse(Complaint.objects.exists())
        self.assertContains(response, 'value="food" selected')

    def test_the_student_page_has_the_form_even_with_no_complaints(self):
        self.login('stu1023')
        response = self.client.get(reverse('complaints:my_complaints'))
        self.assertContains(response, 'Raise a complaint')
        self.assertContains(response, 'You have not raised any complaints')
        self.assertContains(response, 'You have no demerit points')

    def test_a_user_without_a_student_record_sees_a_friendly_message(self):
        user = get_user_model().objects.create_user(username='lonely', password='x')
        UserAccount.objects.create(user=user, role='student')
        self.client.force_login(user)
        response = self.client.get(reverse('complaints:my_complaints'))
        self.assertContains(response, 'student record has not been created yet')

    # --- FR-06.12: students see only their own data -----------------------------------------
    def test_a_student_only_sees_their_own_complaints_and_demerits(self):
        self.complain()
        self.complain(student=self.divya, description='Divya secret text')
        services.log_misconduct(self.arjun, 'moderate', 'Loud music', self.warden)
        self.login('stu1023')
        response = self.client.get(reverse('complaints:my_complaints'))
        self.assertContains(response, 'Fan not working')
        self.assertNotContains(response, 'Divya secret text')
        self.assertEqual(response.context['demerit_total'], 3)
        self.assertContains(response, 'Moderate misconduct: Loud music')

    def test_a_student_cannot_open_someone_elses_complaint(self):
        theirs = self.complain(student=self.divya)
        self.login('stu1023')
        self.assertEqual(self.client.get(reverse('complaints:detail', args=[theirs.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('complaints:edit', args=[theirs.pk])).status_code, 404)

    def test_a_student_can_open_their_own_complaint_with_its_history(self):
        c = self.complain()
        services.change_status(c, 'under_review', 'We are checking', self.warden)
        self.login('stu1023')
        response = self.client.get(reverse('complaints:detail', args=[c.pk]))
        self.assertContains(response, 'Under Review')
        self.assertContains(response, 'We are checking')
        self.assertNotContains(response, 'Update status')       # staff panel is hidden
        self.assertContains(response, 'Edit complaint')

    # --- ST_12_Comp: edit lock --------------------------------------------------------------
    def test_a_student_can_edit_an_open_complaint(self):
        c = self.complain()
        self.login('stu1023')
        response = self.client.post(reverse('complaints:edit', args=[c.pk]),
                                    {'category': 'food', 'description': 'Changed text'}, follow=True)
        c.refresh_from_db()
        self.assertEqual((c.description, c.category), ('Changed text', 'food'))
        self.assertIn(f'Complaint {c.complaint_id} updated', self.shown(response))

    def test_st_12_a_resolved_complaint_cannot_be_edited_by_the_student(self):
        c = self.complain()
        services.change_status(c, 'resolved', 'Done', self.warden)
        self.login('stu1023')
        response = self.client.get(reverse('complaints:edit', args=[c.pk]), follow=True)
        self.assertIn('A resolved complaint cannot be edited; reopen it first', self.shown(response))
        response = self.client.post(reverse('complaints:edit', args=[c.pk]),
                                    {'category': 'food', 'description': 'Sneaky edit'}, follow=True)
        self.assertIn('A resolved complaint cannot be edited; reopen it first', self.shown(response))
        c.refresh_from_db()
        self.assertEqual(c.description, 'Fan not working')
        page = self.client.get(reverse('complaints:detail', args=[c.pk]))
        self.assertContains(page, 'resolved and locked')
        self.assertNotContains(page, 'Edit complaint')

    def test_a_student_cannot_edit_a_misconduct_case(self):
        case = services.log_misconduct(self.arjun, 'minor', 'Noise', self.warden)
        self.login('stu1023')
        self.assertEqual(self.client.get(reverse('complaints:edit', args=[case.pk])).status_code, 404)

    # --- UT_18_Comp: warden filters ---------------------------------------------------------
    def test_ut_18_warden_lists_all_open_complaints_with_student_and_category(self):
        self.complain()
        done = self.complain(student=self.divya, category='food', description='Cold food')
        services.change_status(done, 'resolved', 'Spoken to the mess', self.warden)
        self.login('wdn05')
        response = self.client.get(reverse('complaints:manage'), {'status': 'open'})
        self.assertContains(response, 'Arjun Rao')
        self.assertContains(response, 'Maintenance')
        self.assertNotContains(response, 'Cold food')
        everything = self.client.get(reverse('complaints:manage'))
        self.assertContains(everything, 'Cold food')

    def test_the_manage_page_shows_counts_and_an_empty_message(self):
        self.login('wdn05')
        response = self.client.get(reverse('complaints:manage'), {'q': 'nothing matches'})
        self.assertContains(response, 'No complaints match these filters')
        self.assertEqual(response.context['counts'], {'open': 0, 'under_review': 0, 'resolved': 0, 'escalated': 0})

    # --- IT_16_Comp, IT_18_Comp: warden logs misconduct ---------------------------------------
    def log(self, **extra):
        data = {'student': self.arjun.pk, 'severity': 'moderate', 'category': 'discipline',
                'description': 'Loud music after 11 pm', **extra}
        return self.client.post(reverse('complaints:log_misconduct'), data, follow=True)

    def test_it_16_logging_a_case_assigns_the_points_for_its_severity(self):
        self.login('wdn05')
        response = self.log(severity='major')
        case = Complaint.objects.get()
        self.assertEqual(case.demerit_records.get().points, 5)
        self.assertEqual(response.redirect_chain[-1][0], reverse('complaints:detail', args=[case.pk]))
        self.assertIn(f'Case {case.complaint_id} logged for Arjun Rao: 5 demerit point(s) added. Total: 5',
                      self.shown(response))

    def test_it_18_points_accumulate_on_the_next_case(self):
        self.login('wdn05')
        self.log(severity='minor')
        self.log(severity='moderate')
        self.assertEqual(services.demerit_total(self.arjun), 4)

    def test_misconduct_needs_a_student_and_a_severity(self):
        self.login('wdn05')
        response = self.log(student='')
        self.assertIn('Student is required', self.shown(response))
        response = self.log(severity='')
        self.assertIn('Severity is required', self.shown(response))
        self.assertFalse(Complaint.objects.exists())

    def test_the_administrator_can_also_log_misconduct(self):
        self.login('admin01')
        self.log(severity='minor')
        self.assertEqual(Complaint.objects.get().raised_by, self.admin)

    # --- IT_17_Comp: status update, student sees it -----------------------------------------
    def test_it_17_resolving_with_remarks_notifies_and_shows_on_the_student_page(self):
        c = self.complain()
        self.login('wdn05')
        response = self.client.post(reverse('complaints:update_status', args=[c.pk]),
                                    {'status': 'resolved', 'remarks': 'Fan replaced'}, follow=True)
        self.assertIn(f'Complaint {c.complaint_id} updated. The student has been notified', self.shown(response))
        self.assertTrue(Notification.objects.filter(recipient=self.arjun.user_account,
                                                    message__contains='Fan replaced').exists())
        self.login('stu1023')
        page = self.client.get(reverse('complaints:detail', args=[c.pk]))
        self.assertContains(page, 'Resolved')
        self.assertContains(page, 'Fan replaced')

    def test_resolving_without_remarks_shows_an_error(self):
        c = self.complain()
        self.login('wdn05')
        response = self.client.post(reverse('complaints:update_status', args=[c.pk]),
                                    {'status': 'resolved', 'remarks': ''}, follow=True)
        self.assertIn('Remarks is required', self.shown(response))
        c.refresh_from_db()
        self.assertEqual(c.status, 'open')

    def test_the_warden_can_reopen_and_escalate(self):
        c = self.complain()
        services.change_status(c, 'resolved', 'Done', self.warden)
        self.login('wdn05')
        page = self.client.get(reverse('complaints:detail', args=[c.pk]))
        self.assertContains(page, 'Reopen complaint')
        self.client.post(reverse('complaints:reopen', args=[c.pk]), {'remarks': 'Still broken'})
        c.refresh_from_db()
        self.assertEqual(c.status, 'open')
        response = self.client.post(reverse('complaints:escalate', args=[c.pk]), {'reason': 'Safety'}, follow=True)
        c.refresh_from_db()
        self.assertTrue(c.is_escalated)
        self.assertIn(f'Complaint {c.complaint_id} escalated to the administrator', self.shown(response))
        self.assertTrue(Notification.objects.filter(recipient=self.admin, message__contains='Safety').exists())

    def test_status_changes_must_be_posted(self):
        c = self.complain()
        self.login('wdn05')
        for name in ('update_status', 'reopen', 'escalate'):
            self.assertEqual(self.client.get(reverse(f'complaints:{name}', args=[c.pk])).status_code, 405, name)

    def test_escalated_complaints_can_be_listed_for_the_administrator(self):
        quiet = self.complain()
        loud = services.log_misconduct(self.arjun, 'major', 'Serious', self.warden)
        self.login('admin01')
        response = self.client.get(reverse('complaints:manage'), {'escalated': '1'})
        self.assertContains(response, loud.complaint_id)
        self.assertNotContains(response, quiet.complaint_id)

    # --- FR-06.05: rules -------------------------------------------------------------------
    def test_staff_can_change_the_demerit_rules(self):
        self.login('wdn05')
        response = self.client.post(reverse('complaints:rules'),
                                    {'points_minor': '2', 'points_moderate': '4', 'points_major': '9'}, follow=True)
        self.assertIn('Demerit rules saved. Existing records keep the points they were given', self.shown(response))
        self.assertEqual({r.severity: r.points for r in services.list_rules()},
                         {'minor': 2, 'moderate': 4, 'major': 9})

    def test_invalid_rule_points_show_an_error_and_save_nothing(self):
        self.login('wdn05')
        response = self.client.post(reverse('complaints:rules'),
                                    {'points_minor': '-3', 'points_moderate': '', 'points_major': 'x'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.shown(response)), 3)
        self.assertEqual({r.severity: r.points for r in services.list_rules()},
                         {'minor': 1, 'moderate': 3, 'major': 5})

    # --- ST_11_Comp: report ---------------------------------------------------------------
    def test_st_11_the_report_groups_complaints_by_category(self):
        self.complain(category='maintenance')
        self.complain(category='maintenance', description='Tap')
        services.log_misconduct(self.arjun, 'minor', 'Noise', self.warden)
        self.login('wdn05')
        response = self.client.get(reverse('complaints:report'))
        rows = {r['category']: r['total'] for r in response.context['summary']['rows']}
        self.assertEqual(rows, {'maintenance': 2, 'discipline': 1, 'food': 0, 'other': 0})
        self.assertContains(response, 'All categories')

    def test_the_report_can_be_downloaded_as_csv(self):
        self.complain(category='food', description='Cold food')
        self.login('wdn05')
        response = self.client.get(reverse('complaints:report'), {'export': 'csv'})
        self.assertEqual(response['Content-Type'], 'text/csv')
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], 'Category,Total,Open,Under Review,Resolved')
        self.assertIn('Food,1,1,0,0', lines)
        self.assertEqual(lines[-1], 'All categories,1,1,0,0')

    def test_the_report_checks_its_dates(self):
        self.login('wdn05')
        response = self.client.get(reverse('complaints:report'), {'start': '2026-10-10', 'end': '2026-10-01'})
        self.assertIn('End date cannot be before Start date', self.shown(response))
        response = self.client.get(reverse('complaints:report'), {'start': 'not-a-date'})
        self.assertIn('Date format is invalid', self.shown(response))
        today = date.today().isoformat()
        self.complain()
        ok = self.client.get(reverse('complaints:report'), {'start': today, 'end': today})
        self.assertEqual(ok.context['summary']['totals']['total'], 1)
