"""FR-04 Room Allocation rules (Issues #53-#65). Test Plan: UT_10-12, IT_10-12, ST_07-08."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from core.models import (Allocation, AllocationRequest, AllocationRule, Hostel, Notification,
                         Room, Student, UserAccount)
from core.notifications import get_notifications
from core.seed import seed

from . import services


class AllocationTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.hostel = Hostel.objects.get(code='MAIN')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.arjun = Student.objects.get(roll_no='CSE2201')   # year 2
        cls.divya = Student.objects.get(roll_no='CSE2202')   # year 2
        cls.a101 = Room.objects.get(room_no='A-101')          # triple
        cls.b204 = Room.objects.get(room_no='B-204')          # double
        cls.c102 = Room.objects.get(room_no='C-102')          # double

    def make_student(self, roll_no, year, name=None, hostel=None):
        user = get_user_model().objects.create(username=roll_no.lower())
        account = UserAccount.objects.create(user=user, role='student', hostel=self.hostel)
        return Student.objects.create(
            user_account=account, hostel=hostel or self.hostel, roll_no=roll_no,
            full_name=name or roll_no, year_of_study=year)

    def fill(self, room, count):
        """Put ``count`` brand-new students into ``room``."""
        for i in range(count):
            student = self.make_student(f'{room.room_no}-F{i}'.replace('-', ''), 1)
            services.allocate(student, room, by=self.warden)


class VacantRoomTests(AllocationTestBase):
    def test_UT_10__only_rooms_with_capacity_are_listed(self):
        self.fill(self.b204, 2)
        rooms = {r.room_no for r in services.vacant_rooms(self.divya)}
        self.assertEqual(rooms, {'A-101', 'C-102'})

    def test_IT_08__full_room_is_not_a_candidate(self):
        self.fill(self.a101, 3)
        self.assertNotIn('A-101', {r.room_no for r in services.vacant_rooms(self.divya)})

    def test_inactive_room_and_other_hostel_rooms_are_not_listed(self):
        Room.objects.filter(pk=self.c102.pk).update(is_active=False)
        other = Hostel.objects.create(name='North', code='NORTH')
        Room.objects.create(hostel=other, room_no='N-1', capacity=2)
        rooms = {r.room_no for r in services.vacant_rooms(self.divya)}
        self.assertEqual(rooms, {'A-101', 'B-204'})

    def test_vacancy_counts_and_ordering(self):
        self.fill(self.b204, 1)  # partly filled room comes before empty rooms
        rooms = services.vacant_rooms(self.divya)
        self.assertEqual(rooms[0].room_no, 'B-204')
        self.assertEqual((rooms[0].occupied_beds, rooms[0].free_beds), (1, 1))

    def test_requested_room_type_comes_first(self):
        services.add_to_waitlist(self.divya, by=self.warden, room_type='triple')
        self.assertEqual(services.vacant_rooms(self.divya)[0].room_no, 'A-101')


class AllocateTests(AllocationTestBase):
    def test_UT_11__allocate_vacant_room(self):
        before = self.b204.vacancies
        allocation = services.allocate(self.divya, self.b204, by=self.warden)
        self.assertEqual(allocation.status, Allocation.STATUS_ACTIVE)
        self.assertEqual(allocation.allocated_by, self.warden)
        self.assertEqual(services.current_allocation(self.divya).room, self.b204)
        self.assertEqual(Room.objects.get(pk=self.b204.pk).vacancies, before - 1)

    def test_IT_10__full_room_is_blocked_with_room_unavailable(self):
        self.fill(self.b204, 2)
        with self.assertRaises(ValidationError) as ctx:
            services.allocate(self.divya, self.b204, by=self.warden)
        self.assertEqual(ctx.exception.messages, ['Room unavailable'])
        self.assertEqual(ctx.exception.code, 'room_unavailable')
        self.assertIsNone(services.current_allocation(self.divya))

    def test_inactive_room_is_blocked(self):
        Room.objects.filter(pk=self.b204.pk).update(is_active=False)
        with self.assertRaises(ValidationError) as ctx:
            services.allocate(self.divya, self.b204, by=self.warden)
        self.assertEqual(ctx.exception.code, 'room_unavailable')

    def test_room_in_another_hostel_is_blocked(self):
        other = Hostel.objects.create(name='North', code='NORTH')
        room = Room.objects.create(hostel=other, room_no='N-1', capacity=2)
        with self.assertRaises(ValidationError):
            services.allocate(self.divya, room, by=self.warden)

    def test_IT_11__second_allocation_requires_transfer(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        with self.assertRaises(ValidationError) as ctx:
            services.allocate(self.divya, self.c102, by=self.warden)
        self.assertEqual(ctx.exception.code, 'already_allocated')
        self.assertIn('transfer', ctx.exception.messages[0])
        self.assertEqual(Allocation.objects.filter(student=self.divya).count(), 1)

    def test_ST_08__no_vacant_rooms_message(self):
        self.fill(self.a101, 3); self.fill(self.b204, 2); self.fill(self.c102, 2)
        with self.assertRaises(ValidationError) as ctx:
            services.allocate(self.divya, self.b204, by=self.warden)
        self.assertEqual(ctx.exception.messages, ['No vacant rooms available'])

    def test_inactive_student_cannot_be_allocated(self):
        Student.objects.filter(pk=self.divya.pk).update(is_active=False)
        self.divya.refresh_from_db()
        with self.assertRaises(ValidationError):
            services.allocate(self.divya, self.b204, by=self.warden)

    def test_stale_vacancy_list_cannot_overfill_the_last_bed(self):
        """FR-04.12: the list showed B-204 with one bed; another warden took it first."""
        self.fill(self.b204, 1)
        stale = [r for r in services.vacant_rooms(self.divya) if r.room_no == 'B-204'][0]
        services.allocate(self.arjun, self.b204, by=self.warden)   # takes the last bed
        with self.assertRaises(ValidationError) as ctx:
            services.allocate(self.divya, stale, by=self.warden)
        self.assertEqual(ctx.exception.code, 'room_unavailable')
        self.assertEqual(Room.objects.get(pk=self.b204.pk).occupancy, 2)

    def test_database_still_allows_only_one_active_allocation_per_student(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Allocation.objects.create(student=self.divya, room=self.c102,
                                      allocated_on=date.today())

    def test_FR_04_09__student_is_notified(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        note = get_notifications(self.divya).get()
        self.assertEqual(note.category, Notification.CATEGORY_ALLOCATION)
        self.assertIn('B-204', note.message)
        self.assertFalse(note.is_read)

    def test_failed_allocation_sends_no_notification(self):
        self.fill(self.b204, 2)
        before = Notification.objects.count()
        with self.assertRaises(ValidationError):
            services.allocate(self.divya, self.b204, by=self.warden)
        self.assertEqual(Notification.objects.count(), before)

    def test_allocation_closes_the_waiting_request(self):
        request = services.add_to_waitlist(self.divya, by=self.warden)
        services.allocate(self.divya, self.b204, by=self.warden)
        request.refresh_from_db()
        self.assertEqual(request.status, AllocationRequest.STATUS_APPROVED)
        self.assertEqual(request.processed_by, self.warden)


class PriorityTests(AllocationTestBase):
    def setUp(self):
        self.senior = self.make_student('CSE2001', 4, 'Senior')
        self.junior = self.make_student('CSE2301', 1, 'Junior')
        self.fill(self.a101, 3); self.fill(self.b204, 1)   # exactly one free bed (B-204)
        self.fill(self.c102, 2)

    def test_default_rule_exists_and_scores_by_year(self):
        self.assertEqual(services.priority_score(self.senior), 4)
        self.assertEqual(services.priority_score(self.junior), 1)

    def test_UT_12__junior_ahead_of_waiting_senior_is_flagged_and_blocked(self):
        services.add_to_waitlist(self.senior, by=self.warden)
        self.assertEqual([c.student for c in services.priority_conflicts(self.junior)],
                         [self.senior])
        with self.assertRaises(ValidationError) as ctx:
            services.allocate(self.junior, self.b204, by=self.warden)
        self.assertEqual(ctx.exception.code, 'priority_conflict')
        self.assertIsNone(services.current_allocation(self.junior))

    def test_senior_is_not_flagged_and_is_allocated(self):
        services.add_to_waitlist(self.junior, by=self.warden)
        self.assertEqual(services.priority_conflicts(self.senior), [])
        services.allocate(self.senior, self.b204, by=self.warden)

    def test_warden_can_override_the_flag(self):
        services.add_to_waitlist(self.senior, by=self.warden)
        services.allocate(self.junior, self.b204, by=self.warden, override_priority=True)
        self.assertEqual(services.current_allocation(self.junior).room, self.b204)

    def test_no_flag_when_there_are_enough_beds_for_everyone(self):
        services.vacate(services.current_allocation(Student.objects.get(roll_no='C102F0')),
                        by=self.warden)               # a second free bed appears
        services.add_to_waitlist(self.senior, by=self.warden)
        self.assertEqual(services.priority_conflicts(self.junior), [])

    def test_equal_priority_does_not_flag(self):
        other = self.make_student('CSE2302', 1)
        services.add_to_waitlist(other, by=self.warden)
        self.assertEqual(services.priority_conflicts(self.junior), [])

    def test_waitlist_is_ordered_by_priority_then_first_come(self):
        second_senior = self.make_student('CSE2002', 4, 'Second senior')
        services.add_to_waitlist(self.junior, by=self.warden)
        services.add_to_waitlist(self.senior, by=self.warden)
        services.add_to_waitlist(second_senior, by=self.warden)
        self.assertEqual([r.student for r in services.waitlist()],
                         [self.senior, second_senior, self.junior])

    def test_changing_rules_rescores_the_waitlist(self):
        services.add_to_waitlist(self.senior, by=self.warden)
        AllocationRule.objects.filter(criterion='seniority').update(weight=10)
        services.recalculate_waitlist_priorities()
        self.assertEqual(AllocationRequest.objects.get(student=self.senior).priority, 40)

    def test_inactive_rule_gives_everyone_equal_priority(self):
        AllocationRule.objects.filter(criterion='seniority').update(is_active=False)
        self.assertEqual(services.priority_score(self.senior), 0)


class TransferTests(AllocationTestBase):
    def test_IT_12__transfer_updates_both_rooms(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        b_before, c_before = self.b204.vacancies, self.c102.vacancies
        services.transfer(self.divya, self.c102, by=self.warden)
        self.assertEqual(services.current_allocation(self.divya).room, self.c102)
        self.assertEqual(Room.objects.get(pk=self.b204.pk).vacancies, b_before + 1)
        self.assertEqual(Room.objects.get(pk=self.c102.pk).vacancies, c_before - 1)

    def test_transfer_keeps_history(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        services.transfer(self.divya, self.c102, by=self.warden)
        old = Allocation.objects.get(student=self.divya, room=self.b204)
        self.assertEqual(old.status, Allocation.STATUS_TRANSFERRED)
        self.assertIsNotNone(old.ended_on)

    def test_transfer_to_full_room_is_blocked_and_nothing_changes(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        self.fill(self.c102, 2)
        with self.assertRaises(ValidationError) as ctx:
            services.transfer(self.divya, self.c102, by=self.warden)
        self.assertEqual(ctx.exception.code, 'room_unavailable')
        self.assertEqual(services.current_allocation(self.divya).room, self.b204)

    def test_transfer_requires_an_existing_allocation(self):
        with self.assertRaises(ValidationError) as ctx:
            services.transfer(self.divya, self.c102, by=self.warden)
        self.assertEqual(ctx.exception.code, 'not_allocated')

    def test_transfer_to_same_room_is_rejected(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        with self.assertRaises(ValidationError) as ctx:
            services.transfer(self.divya, self.b204, by=self.warden)
        self.assertEqual(ctx.exception.code, 'same_room')

    def test_transfer_notifies_the_student(self):
        services.allocate(self.divya, self.b204, by=self.warden)
        services.transfer(self.divya, self.c102, by=self.warden)
        latest = get_notifications(self.divya).first()
        self.assertIn('B-204', latest.message)
        self.assertIn('C-102', latest.message)

    def test_transfer_can_fill_the_room_freed_by_another_student(self):
        self.fill(self.b204, 1)
        services.allocate(self.divya, self.c102, by=self.warden)
        services.transfer(self.divya, self.b204, by=self.warden)
        self.assertEqual(Room.objects.get(pk=self.b204.pk).occupancy, 2)


class VacateAndWaitlistTests(AllocationTestBase):
    def test_vacate_frees_the_bed(self):
        allocation = services.allocate(self.divya, self.b204, by=self.warden)
        services.vacate(allocation, by=self.warden)
        allocation.refresh_from_db()
        self.assertEqual(allocation.status, Allocation.STATUS_ENDED)
        self.assertEqual(allocation.ended_on, date.today())
        self.assertEqual(Room.objects.get(pk=self.b204.pk).occupancy, 0)
        self.assertIsNone(services.current_allocation(self.divya))

    def test_vacated_student_can_be_allocated_again(self):
        services.vacate(services.allocate(self.divya, self.b204, by=self.warden), by=self.warden)
        services.allocate(self.divya, self.c102, by=self.warden)
        self.assertEqual(Allocation.objects.filter(student=self.divya).count(), 2)

    def test_cannot_vacate_twice(self):
        allocation = services.allocate(self.divya, self.b204, by=self.warden)
        services.vacate(allocation, by=self.warden)
        with self.assertRaises(ValidationError):
            services.vacate(allocation, by=self.warden)

    def test_add_and_remove_waitlist(self):
        request = services.add_to_waitlist(self.divya, by=self.warden, room_type=' Double ')
        self.assertEqual(request.requested_room_type, 'Double')
        self.assertEqual(request.priority, 2)
        self.assertTrue(services.remove_from_waitlist(request, by=self.warden))
        self.assertEqual(list(services.waitlist()), [])
        self.assertFalse(services.remove_from_waitlist(request, by=self.warden))

    def test_cannot_join_waitlist_twice_or_when_allocated(self):
        services.add_to_waitlist(self.divya, by=self.warden)
        with self.assertRaises(ValidationError) as ctx:
            services.add_to_waitlist(self.divya, by=self.warden)
        self.assertEqual(ctx.exception.code, 'already_waiting')
        services.allocate(self.arjun, self.b204, by=self.warden)
        with self.assertRaises(ValidationError) as ctx:
            services.add_to_waitlist(self.arjun, by=self.warden)
        self.assertEqual(ctx.exception.code, 'already_allocated')

    def test_unallocated_students(self):
        services.allocate(self.arjun, self.b204, by=self.warden)
        self.assertEqual(list(services.unallocated_students()), [self.divya])


class ReportTests(AllocationTestBase):
    def test_ST_07__report_lists_students_rooms_and_dates(self):
        services.allocate(self.arjun, self.b204, by=self.warden)
        services.allocate(self.divya, self.c102, by=self.warden)
        rows = list(services.allocation_report())
        self.assertEqual({(r.student.roll_no, r.room.room_no) for r in rows},
                         {('CSE2201', 'B-204'), ('CSE2202', 'C-102')})

    def test_date_range_and_status_filters(self):
        today = date.today()
        old = services.allocate(self.arjun, self.b204, by=self.warden,
                                today=today - timedelta(days=60))
        services.vacate(old, by=self.warden, today=today - timedelta(days=30))
        services.allocate(self.divya, self.c102, by=self.warden)
        recent = services.allocation_report(start=today - timedelta(days=7), end=today)
        self.assertEqual([r.student for r in recent], [self.divya])
        earlier = services.allocation_report(end=today - timedelta(days=40))
        self.assertEqual([r.student for r in earlier], [self.arjun])
        ended = services.allocation_report(status=Allocation.STATUS_ENDED)
        self.assertEqual([r.student for r in ended], [self.arjun])
