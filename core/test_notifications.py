import importlib
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import SimpleTestCase, TestCase

from .error_messages import msg
from .models import Hostel, Notification, Student, UserAccount
from .notifications import (
    get_notifications,
    mark_all_read,
    mark_read,
    mark_unread,
    notify,
    unread_count,
)


def make_account(hostel, username, role=UserAccount.ROLE_STUDENT):
    user = get_user_model().objects.create(username=username)
    return UserAccount.objects.create(user=user, role=role, hostel=hostel)


def make_student(hostel, username, roll_no, name):
    account = make_account(hostel, username)
    return Student.objects.create(
        user_account=account, hostel=hostel, roll_no=roll_no, full_name=name,
        phone='9876543210', course='CSE', year_of_study=2)


class NotificationTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hostel = Hostel.objects.create(name='Main Hostel', code='MAIN')
        cls.arjun = make_student(cls.hostel, 'stu1023', 'CSE2201', 'Arjun Rao')
        cls.divya = make_student(cls.hostel, 'stu1024', 'CSE2202', 'Divya S.')
        cls.warden = make_account(cls.hostel, 'wdn05', UserAccount.ROLE_WARDEN)


class NotifyTests(NotificationTestBase):
    def test_notify_saves_an_unread_notification_for_the_student(self):
        note = notify(self.arjun, 'ALLOCATION', 'You have been allocated room A-101')
        saved = Notification.objects.get(pk=note.pk)
        self.assertEqual(saved.recipient, self.arjun.user_account)
        self.assertEqual(saved.category, 'ALLOCATION')
        self.assertEqual(saved.message, 'You have been allocated room A-101')
        self.assertFalse(saved.is_read)
        self.assertIsNotNone(saved.created_at)

    def test_notify_accepts_a_user_account_such_as_a_warden(self):
        note = notify(self.warden, 'COMPLAINT', 'A new complaint needs action')
        self.assertEqual(note.recipient, self.warden)

    def test_all_module_categories_are_accepted(self):
        for category in ('ALLOCATION', 'FEE', 'LEAVE', 'COMPLAINT', 'NOTICE'):
            with self.subTest(category=category):
                self.assertEqual(notify(self.arjun, category, 'hello').category, category)

    def test_category_is_case_insensitive_and_message_is_trimmed(self):
        note = notify(self.arjun, ' leave ', '   Leave approved   ')
        self.assertEqual(note.category, 'LEAVE')
        self.assertEqual(note.message, 'Leave approved')

    def test_blank_message_is_rejected_with_standard_message(self):
        for blank in ('', '   ', None):
            with self.subTest(blank=blank):
                with self.assertRaises(ValidationError) as ctx:
                    notify(self.arjun, 'FEE', blank)
                self.assertEqual(ctx.exception.messages, ['Message is required'])
        self.assertEqual(Notification.objects.count(), 0)

    def test_unknown_category_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            notify(self.arjun, 'SPAM', 'hello')
        self.assertEqual(ctx.exception.messages, ['Notification type is not a valid choice'])
        self.assertEqual(Notification.objects.count(), 0)

    def test_message_longer_than_255_characters_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            notify(self.arjun, 'FEE', 'x' * 256)
        self.assertEqual(ctx.exception.messages, ['Message must be at most 255 characters'])
        notify(self.arjun, 'FEE', 'x' * 255)

    def test_all_problems_are_reported_together(self):
        with self.assertRaises(ValidationError) as ctx:
            notify(self.arjun, '', '')
        self.assertEqual(set(ctx.exception.error_dict), {'category', 'message'})
        self.assertIn('Notification type is required', ctx.exception.messages)
        self.assertIn('Message is required', ctx.exception.messages)

    def test_wrong_target_type_is_a_programming_error(self):
        with self.assertRaises(TypeError):
            notify('stu1023', 'FEE', 'hello')


class ReadStateTests(NotificationTestBase):
    def setUp(self):
        self.first = notify(self.arjun, 'ALLOCATION', 'First')
        self.second = notify(self.arjun, 'FEE', 'Second')
        self.other = notify(self.divya, 'LEAVE', 'For Divya')

    def test_new_notifications_are_unread(self):
        self.assertEqual(unread_count(self.arjun), 2)
        self.assertEqual(unread_count(self.divya), 1)

    def test_list_is_newest_first_and_can_filter_unread(self):
        self.assertEqual([n.message for n in get_notifications(self.arjun)], ['Second', 'First'])
        mark_read(self.arjun, self.second.pk)
        self.assertEqual([n.message for n in get_notifications(self.arjun, unread_only=True)], ['First'])

    def test_each_user_sees_only_their_own_notifications(self):
        messages = [n.message for n in get_notifications(self.divya)]
        self.assertEqual(messages, ['For Divya'])

    def test_mark_read_and_mark_unread_are_persisted(self):
        self.assertTrue(mark_read(self.arjun, self.first.pk))
        self.first.refresh_from_db()
        self.assertTrue(self.first.is_read)
        self.assertEqual(unread_count(self.arjun), 1)
        self.assertTrue(mark_unread(self.arjun, self.first.pk))
        self.first.refresh_from_db()
        self.assertFalse(self.first.is_read)
        self.assertEqual(unread_count(self.arjun), 2)

    def test_a_user_cannot_mark_someone_elses_notification(self):
        self.assertFalse(mark_read(self.divya, self.first.pk))
        self.first.refresh_from_db()
        self.assertFalse(self.first.is_read)

    def test_unknown_notification_returns_false(self):
        self.assertFalse(mark_read(self.arjun, 999999))

    def test_mark_all_read_only_affects_that_user(self):
        self.assertEqual(mark_all_read(self.arjun), 2)
        self.assertEqual(unread_count(self.arjun), 0)
        self.assertEqual(unread_count(self.divya), 1)
        self.assertEqual(mark_all_read(self.arjun), 0)

    def test_student_or_account_can_be_used_to_read(self):
        self.assertEqual(unread_count(self.arjun.user_account), unread_count(self.arjun))


class NotificationMessagesTests(SimpleTestCase):
    def test_new_catalogue_messages(self):
        self.assertEqual(msg('max_length', field='Message', limit=255),
                         'Message must be at most 255 characters')
        self.assertEqual(msg('invalid_choice', field='Notification type'),
                         'Notification type is not a valid choice')


class NotificationTableTests(TestCase):
    def test_table_exists_after_migrating(self):
        self.assertIn(Notification._meta.db_table, connection.introspection.table_names())

    def test_migration_skips_creation_when_table_already_exists(self):
        migration = importlib.import_module('core.migrations.0002_notification')
        editor = SimpleNamespace(connection=connection, create_model=Mock())
        migration.create_notification_table(None, editor)
        editor.create_model.assert_not_called()

    def test_migration_creates_the_table_when_it_is_missing(self):
        migration = importlib.import_module('core.migrations.0002_notification')
        editor = SimpleNamespace(connection=connection, create_model=Mock())
        with patch.object(connection.introspection, 'table_names', return_value=[]):
            migration.create_notification_table(None, editor)
        editor.create_model.assert_called_once_with(Notification)
