"""Unit tests for Notice / Information Management services (FR-10)."""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.models import Notice, Student, UserAccount
from core.seed import seed
from notices import services


class NoticeServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.arjun = Student.objects.get(roll_no='CSE2201')
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')

    # --- UT_28_Notice: Verify warden/administrator can create a new notice ---
    def test_UT_28_Notice__create_notice_with_timestamp(self):
        """Title: 'Hostel Maintenance', Content: 'Water supply off 9-11 AM' is stored with timestamp."""
        before = timezone.now()
        notice = services.publish_notice(
            title='Hostel Maintenance',
            body='Water supply off 9-11 AM',
            author=self.warden,
            audience='all',
        )
        notice.refresh_from_db()

        self.assertEqual(notice.title, 'Hostel Maintenance')
        self.assertEqual(notice.body, 'Water supply off 9-11 AM')
        self.assertEqual(notice.published_by, self.warden)
        self.assertTrue(notice.is_published)
        self.assertIsNotNone(notice.published_at)
        self.assertTrue(before <= notice.published_at <= timezone.now())

    # --- UT_29_Notice: Verify notice creation fails with an empty title or content ---
    def test_UT_29_Notice__empty_title_fails(self):
        """Blank title raises validation error."""
        with self.assertRaises(ValidationError) as ctx:
            services.publish_notice(
                title='   ',
                body='Some content',
                author=self.admin,
            )
        self.assertIn('Title is required', str(ctx.exception))

    def test_UT_29_Notice__empty_content_fails(self):
        """Blank content raises validation error."""
        with self.assertRaises(ValidationError) as ctx:
            services.publish_notice(
                title='Some Title',
                body='',
                author=self.admin,
            )
        self.assertIn('Content is required', str(ctx.exception))

    # --- FR-10.04 & UT_30: Target audience for notices ---
    def test_FR_10_04__target_audience_filtering(self):
        """Wardens-only notices are not visible to students."""
        services.publish_notice(
            title='Warden Meeting',
            body='Monthly warden review',
            author=self.admin,
            audience='wardens',
        )
        services.publish_notice(
            title='Student Mess Notice',
            body='Mess fee deadline',
            author=self.warden,
            audience='students',
        )

        student_notices = services.get_active_notices(role=UserAccount.ROLE_STUDENT)
        student_titles = [n.title for n in student_notices]
        self.assertIn('Student Mess Notice', student_titles)
        self.assertNotIn('Warden Meeting', student_titles)

        warden_notices = services.get_active_notices(role=UserAccount.ROLE_WARDEN)
        warden_titles = [n.title for n in warden_notices]
        self.assertIn('Warden Meeting', warden_titles)
        self.assertNotIn('Student Mess Notice', warden_titles)

    # --- IT_28_Notice: Verify editing an existing notice updates content ---
    def test_IT_28_Notice__update_existing_notice(self):
        """Updating title and body modifies the notice content."""
        notice = services.publish_notice(
            title='Initial Notice',
            body='Initial content',
            author=self.warden,
        )
        updated = services.update_notice(
            notice,
            title='Updated Title',
            body='Revised timing: 10-12 PM',
        )
        updated.refresh_from_db()
        self.assertEqual(updated.title, 'Updated Title')
        self.assertEqual(updated.body, 'Revised timing: 10-12 PM')

    # --- IT_29_Notice: Verify deleting or expiring a notice removes it ---
    def test_IT_29_Notice__delete_and_expire(self):
        """Deleted or expired notices no longer appear in active notices."""
        n1 = services.publish_notice('Notice to delete', 'Body', author=self.admin)
        n2 = services.publish_notice('Notice to expire', 'Body', author=self.admin)

        services.delete_notice(n1)
        services.expire_notice(n2)

        active = services.get_active_notices()
        active_ids = [n.id for n in active]
        self.assertNotIn(n1.id, active_ids)
        self.assertNotIn(n2.id, active_ids)

    # --- IT_30_Notice: Verify notices are ordered newest first ---
    def test_IT_30_Notice__order_newest_first(self):
        """Notices are returned in descending chronological order."""
        t1 = timezone.now() - timedelta(days=2)
        t2 = timezone.now() - timedelta(days=1)
        t3 = timezone.now()

        n1 = Notice.objects.create(title='First', body='B1', published_by=self.warden, is_published=True, published_at=t1)
        n2 = Notice.objects.create(title='Second', body='B2', published_by=self.warden, is_published=True, published_at=t2)
        n3 = Notice.objects.create(title='Third', body='B3', published_by=self.warden, is_published=True, published_at=t3)

        notices = list(services.get_active_notices())
        self.assertEqual(notices[0].id, n3.id)
        self.assertEqual(notices[1].id, n2.id)
        self.assertEqual(notices[2].id, n1.id)

    # --- ST_19_Notice: Search notices by keyword ---
    def test_ST_19_Notice__search_by_keyword(self):
        """Keyword 'Maintenance' returns only matching notices."""
        n_match = services.publish_notice('Hostel Maintenance', 'Water pipe repair', author=self.warden)
        n_other = services.publish_notice('Cultural Fest', 'Music and drama', author=self.warden)

        results = services.search_notices(keyword='Maintenance')
        self.assertIn(n_match, results)
        self.assertNotIn(n_other, results)
