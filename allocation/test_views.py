"""FR-04 screens: warden allocation, transfer, waitlist, rules, report; student My Room."""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Allocation, AllocationRule, Room, Student, UserAccount
from core.seed import seed

from . import services


class AllocationViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.divya = Student.objects.get(roll_no='CSE2202')
        cls.b204 = Room.objects.get(room_no='B-204')
        cls.c102 = Room.objects.get(room_no='C-102')
        cls.a101 = Room.objects.get(room_no='A-101')

    def setUp(self):
        self.client.force_login(self.warden.user)

    def allocate(self, student, room, **extra):
        return self.client.post(reverse('allocation:allocate'),
                                {'student': student.pk, 'room': room.pk, **extra}, follow=True)

    def shown(self, response):
        return [str(m) for m in response.context['messages']]

    # --- access ----------------------------------------------------------------------
    def test_only_wardens_can_use_the_warden_screens(self):
        names = ['manage', 'waitlist', 'rules', 'report']
        for username in ('stu1023', 'admin01'):
            self.client.force_login(get_user_model().objects.get(username=username))
            for name in names:
                with self.subTest(username=username, url=name):
                    self.assertEqual(self.client.get(reverse(f'allocation:{name}')).status_code, 403)
            self.assertEqual(self.client.post(reverse('allocation:allocate')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('allocation:manage')).status_code, 302)

    def test_actions_reject_get_requests(self):
        for url in (reverse('allocation:allocate'), reverse('allocation:waitlist_add')):
            self.assertEqual(self.client.get(url).status_code, 405)

    def test_menu_links_are_live_for_warden_and_student(self):
        response = self.client.get(reverse('core:dashboard_warden'))
        item = next(i for i in response.context['nav_items'] if i['label'] == 'Room Allocation')
        self.assertEqual(item['url'], reverse('allocation:manage'))
        self.client.force_login(get_user_model().objects.get(username='stu1023'))
        response = self.client.get(reverse('core:dashboard_student'))
        item = next(i for i in response.context['nav_items'] if i['label'] == 'My Room')
        self.assertEqual(item['url'], reverse('allocation:my_room'))

    # --- FR-04.01 / UT_10 --------------------------------------------------------------
    def test_UT_10__selecting_a_student_lists_only_vacant_rooms(self):
        services.allocate(self.arjun, self.b204, by=self.warden)
        for student in (Student.objects.create(
                user_account=UserAccount.objects.create(
                    user=get_user_model().objects.create(username='filler'), role='student',
                    hostel=self.divya.hostel),
                hostel=self.divya.hostel, roll_no='FILL1', full_name='Filler', year_of_study=1),):
            services.allocate(student, self.b204, by=self.warden)   # B-204 now full
        response = self.client.get(reverse('allocation:manage'), {'student': self.divya.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual({r.room_no for r in response.context['vacant_rooms']}, {'A-101', 'C-102'})
        self.assertContains(response, 'A-101')
        self.assertNotContains(response, '>B-204<')

    def test_manage_page_without_a_student_or_with_a_bad_id(self):
        self.assertEqual(self.client.get(reverse('allocation:manage')).status_code, 200)
        response = self.client.get(reverse('allocation:manage'), {'student': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['selected'])

    # --- FR-04.02 / UT_11 --------------------------------------------------------------
    def test_UT_11__allocate_shows_room_on_student_record(self):
        response = self.allocate(self.divya, self.b204)
        self.assertIn('Room B-204 allocated to Divya S.', self.shown(response))
        self.assertEqual(response.context['allocation'].room, self.b204)
        self.assertContains(response, 'Currently in room')

    # --- FR-04.06 / IT_10, FR-04.10 / ST_08 ---------------------------------------------
    def test_IT_10__full_room_shows_room_unavailable_and_refreshes_list(self):
        for i in range(2):
            student = Student.objects.create(
                user_account=UserAccount.objects.create(
                    user=get_user_model().objects.create(username=f'f{i}'), role='student',
                    hostel=self.divya.hostel),
                hostel=self.divya.hostel, roll_no=f'F{i}', full_name=f'F{i}', year_of_study=1)
            services.allocate(student, self.b204, by=self.warden)
        response = self.allocate(self.divya, self.b204)
        self.assertIn('Room unavailable', self.shown(response))
        self.assertNotIn(self.b204, response.context['vacant_rooms'])   # list refreshed
        self.assertIsNone(services.current_allocation(self.divya))

    def test_ST_08__no_vacant_rooms_is_shown_without_an_error(self):
        Room.objects.update(is_active=False)
        response = self.client.get(reverse('allocation:manage'), {'student': self.divya.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No vacant rooms available')
        self.assertContains(response, 'to the waitlist')

    # --- FR-04.07 / IT_11 and FR-04.08 / IT_12 ---------------------------------------------
    def test_IT_11__allocating_an_allocated_student_redirects_to_transfer(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        response = self.client.post(reverse('allocation:allocate'),
                                    {'student': self.divya.pk, 'room': self.c102.pk})
        self.assertRedirects(
            response, f"{reverse('allocation:transfer', args=[self.divya.pk])}?room={self.c102.pk}")
        self.assertEqual(Allocation.objects.filter(student=self.divya).count(), 1)

    def test_IT_12__transfer_needs_confirmation_then_moves_the_student(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        url = reverse('allocation:transfer', args=[self.divya.pk])
        page = self.client.get(url, {'room': self.c102.pk})
        self.assertContains(page, 'Confirm transfer')
        self.assertEqual(services.current_allocation(self.divya).room, self.b204)  # not saved yet
        response = self.client.post(url, {'room': self.c102.pk}, follow=True)
        self.assertIn('Divya S. moved from B-204 to C-102', self.shown(response))
        self.assertEqual(services.current_allocation(self.divya).room, self.c102)

    def test_transfer_page_for_unallocated_student_goes_back_with_error(self):
        response = self.client.get(reverse('allocation:transfer', args=[self.divya.pk]),
                                   follow=True)
        self.assertIn('Student does not have a room allocated', self.shown(response))

    def test_transfer_to_the_current_or_unknown_room_is_not_confirmable(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        url = reverse('allocation:transfer', args=[self.divya.pk])
        for room in (self.b204.pk, 99999):
            response = self.client.post(url, {'room': room})
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.context['target'])
            self.assertEqual(services.current_allocation(self.divya).room, self.b204)

    # --- FR-04.04 priority flag ---------------------------------------------------------------
    def test_priority_flag_is_shown_and_override_allocates(self):
        for room in (self.a101, self.c102):
            Room.objects.filter(pk=room.pk).update(is_active=False)
        senior_user = get_user_model().objects.create(username='senior')
        senior = Student.objects.create(
            user_account=UserAccount.objects.create(user=senior_user, role='student',
                                                    hostel=self.divya.hostel),
            hostel=self.divya.hostel, roll_no='SEN1', full_name='Sam Senior', year_of_study=4)
        services.add_to_waitlist(senior, by=self.warden)
        Room.objects.filter(pk=self.b204.pk).update(capacity=1)
        page = self.client.get(reverse('allocation:manage'), {'student': self.divya.pk})
        self.assertContains(page, 'Priority flag')
        self.assertContains(page, 'Sam Senior')
        blocked = self.allocate(self.divya, self.b204)
        self.assertIn('A higher-priority student is waiting for a room', self.shown(blocked))
        self.assertIsNone(services.current_allocation(self.divya))
        self.allocate(self.divya, self.b204, override='1')
        self.assertEqual(services.current_allocation(self.divya).room, self.b204)

    # --- FR-04.13 vacate ------------------------------------------------------------------------
    def test_release_room(self):
        allocation = services.allocate(self.divya, self.b204, by=self.warden)
        response = self.client.post(reverse('allocation:vacate', args=[allocation.pk]), follow=True)
        self.assertIn('Room B-204 released by Divya S.', self.shown(response))
        self.assertEqual(Room.objects.get(pk=self.b204.pk).occupancy, 0)

    # --- FR-04.05 waitlist ---------------------------------------------------------------------
    def test_waitlist_add_and_remove(self):
        response = self.client.post(reverse('allocation:waitlist_add'),
                                    {'student': self.divya.pk, 'room_type': 'Double'}, follow=True)
        self.assertIn('Divya S. added to the waitlist', self.shown(response))
        self.assertContains(response, 'CSE2202')
        again = self.client.post(reverse('allocation:waitlist_add'),
                                 {'student': self.divya.pk}, follow=True)
        self.assertIn('Student is already on the waitlist', self.shown(again))
        item = services.waitlist().get()
        removed = self.client.post(reverse('allocation:waitlist_remove', args=[item.pk]),
                                   follow=True)
        self.assertIn('Divya S. removed from the waitlist', self.shown(removed))
        self.assertContains(removed, 'The waitlist is empty')

    # --- FR-04.03 rules ------------------------------------------------------------------------
    def test_rules_are_editable_and_rescore_the_waitlist(self):
        services.add_to_waitlist(self.divya, by=self.warden)
        page = self.client.get(reverse('allocation:rules'))
        rule = AllocationRule.objects.get()
        data = {'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '1', 'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000', 'form-0-id': rule.pk, 'form-0-weight': '5',
                'form-0-is_active': 'on', 'form-0-description': 'Seniors first'}
        self.assertEqual(page.status_code, 200)
        response = self.client.post(reverse('allocation:rules'), data, follow=True)
        self.assertIn('Priority rules saved; 1 waiting request(s) re-ordered', self.shown(response))
        rule.refresh_from_db()
        self.assertEqual((rule.weight, rule.description), (5, 'Seniors first'))
        self.assertEqual(services.waitlist().get().priority, 10)   # year 2 x weight 5

    def test_rule_weight_is_validated(self):
        services.ensure_default_rules()
        rule = AllocationRule.objects.get()
        data = {'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '1', 'form-MIN_NUM_FORMS': '0',
                'form-MAX_NUM_FORMS': '1000', 'form-0-id': rule.pk, 'form-0-weight': '-3',
                'form-0-is_active': 'on', 'form-0-description': ''}
        response = self.client.post(reverse('allocation:rules'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-danger')
        rule.refresh_from_db()
        self.assertEqual(rule.weight, 1)

    # --- FR-04.11 / ST_07 report ----------------------------------------------------------------
    def test_ST_07__report_and_csv_export(self):
        services.allocate(self.arjun, self.b204, by=self.warden)
        services.allocate(self.divya, self.c102, by=self.warden)
        today = date.today().isoformat()
        page = self.client.get(reverse('allocation:report'), {'start': today, 'end': today})
        self.assertContains(page, 'CSE2201')
        self.assertContains(page, 'C-102')
        csv_response = self.client.get(reverse('allocation:report'), {'export': 'csv'})
        self.assertEqual(csv_response['Content-Type'], 'text/csv')
        lines = csv_response.content.decode().strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith('Roll no,Student'))

    def test_report_rejects_an_end_date_before_the_start_date(self):
        response = self.client.get(reverse('allocation:report'),
                                   {'start': '2026-10-10', 'end': '2026-10-01'})
        self.assertIn('End date cannot be before Start date', self.shown(response))
        self.assertIsNone(response.context['rows'])

    def test_csv_cells_that_look_like_formulas_are_neutralised(self):
        Student.objects.filter(pk=self.divya.pk).update(full_name='=HYPERLINK("x")')
        self.divya.refresh_from_db()
        services.allocate(self.divya, self.b204, by=self.warden)
        body = self.client.get(reverse('allocation:report'), {'export': 'csv'}).content.decode()
        self.assertIn("'=HYPERLINK", body)

    # --- student: My Room ----------------------------------------------------------------------
    def test_student_without_a_room_sees_a_friendly_message(self):
        self.client.force_login(self.divya.user_account.user)
        response = self.client.get(reverse('allocation:my_room'))
        self.assertContains(response, 'not been allocated a room yet')

    def test_wardens_cannot_open_my_room(self):
        self.assertEqual(self.client.get(reverse('allocation:my_room')).status_code, 403)
