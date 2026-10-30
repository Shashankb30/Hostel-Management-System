"""Integration and view tests for Notice / Information Management (FR-10)."""
from django.test import TestCase
from django.urls import reverse

from core.models import Notice, UserAccount
from core.seed import seed
from notices import services


class NoticeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.warden = UserAccount.objects.get(user__username='wdn05')
        cls.admin = UserAccount.objects.get(user__username='admin01')
        cls.student = UserAccount.objects.get(user__username='stu1023')

    # --- UT_28_Notice: Verify warden/administrator can create a new notice ---
    def test_UT_28_Notice__warden_creates_new_notice(self):
        """Warden navigates to notice creation, enters title and content, and publishes."""
        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.post(reverse('notices:add'), {
            'title': 'Hostel Maintenance',
            'body': 'Water supply off 9-11 AM',
            'audience': 'all',
            'is_published': 'on',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('notices:manage'))
        self.assertContains(response, 'created successfully')

        notice = Notice.objects.get(title='Hostel Maintenance')
        self.assertEqual(notice.body, 'Water supply off 9-11 AM')
        self.assertTrue(notice.is_published)
        self.assertIsNotNone(notice.published_at)

    # --- UT_29_Notice: Verify notice creation fails with an empty title ---
    def test_UT_29_Notice__empty_title_displays_validation_error(self):
        """Blank title displays validation error and blocks publishing."""
        self.client.login(username='admin01', password='Admin@12')
        initial_count = Notice.objects.count()

        response = self.client.post(reverse('notices:add'), {
            'title': '',
            'body': 'Content without title',
            'audience': 'all',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Title is required')
        self.assertEqual(Notice.objects.count(), initial_count)

    # --- UT_30_Notice: Verify published notice appears on the student dashboard ---
    def test_UT_30_Notice__notice_appears_on_student_dashboard(self):
        """Published notice 'Hostel Maintenance' is visible on the student's dashboard."""
        services.publish_notice(
            title='Hostel Maintenance',
            body='Water supply off 9-11 AM',
            author=self.warden,
            audience='all',
        )

        self.client.login(username='stu1023', password='Pass@123')
        response = self.client.get(reverse('core:dashboard_student'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hostel Maintenance')
        self.assertContains(response, 'Water supply off 9-11 AM')

    # --- IT_28_Notice: Verify editing an existing notice updates the displayed content ---
    def test_IT_28_Notice__editing_updates_content(self):
        """Editing notice content updates what students see on the board."""
        notice = services.publish_notice('Exam Timetable', 'Old content', author=self.admin)

        self.client.login(username='admin01', password='Admin@12')
        response = self.client.post(reverse('notices:edit', args=[notice.pk]), {
            'title': 'Exam Timetable',
            'body': 'Updated exam timetable for semester 2',
            'audience': 'all',
            'is_published': 'on',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('notices:manage'))
        notice.refresh_from_db()
        self.assertEqual(notice.body, 'Updated exam timetable for semester 2')

        # Student views notice board
        self.client.logout()
        self.client.login(username='stu1023', password='Pass@123')
        board_resp = self.client.get(reverse('notices:board'))
        self.assertContains(board_resp, 'Updated exam timetable for semester 2')

    # --- IT_29_Notice: Verify deleting/expiring a notice removes it from student view ---
    def test_IT_29_Notice__deleting_or_expiring_removes_from_view(self):
        """Deleted or expired notice no longer appears on student board or dashboard."""
        notice = services.publish_notice('Expiring Alert', 'Power shutdown', author=self.warden)

        self.client.login(username='wdn05', password='Warden@12')
        self.client.post(reverse('notices:expire', args=[notice.pk]))

        self.client.logout()
        self.client.login(username='stu1023', password='Pass@123')
        resp = self.client.get(reverse('notices:board'))
        self.assertNotContains(resp, 'Expiring Alert')

    # --- IT_30_Notice: Verify notices are ordered by most recent first ---
    def test_IT_30_Notice__order_most_recent_first(self):
        """Notices display in descending order of publish date."""
        services.publish_notice('Older Notice', 'Older body', author=self.warden)
        services.publish_notice('Newer Notice', 'Newer body', author=self.warden)

        self.client.login(username='stu1023', password='Pass@123')
        response = self.client.get(reverse('notices:board'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        pos_newer = content.find('Newer Notice')
        pos_older = content.find('Older Notice')
        self.assertTrue(pos_newer < pos_older, 'Newer notice should appear before older notice')

    # --- ST_19_Notice: Verify notice list can be filtered/searched by keyword ---
    def test_ST_19_Notice__search_by_keyword(self):
        """Keyword 'Maintenance' returns only matching notices."""
        services.publish_notice('Hostel Maintenance', 'Tank cleaning', author=self.warden)
        services.publish_notice('Sports Day', 'Tournament registrations', author=self.warden)

        self.client.login(username='wdn05', password='Warden@12')
        response = self.client.get(reverse('notices:manage'), {'q': 'Maintenance'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hostel Maintenance')
        self.assertNotContains(response, 'Sports Day')

    # --- ST_20_Notice: Verify only authorized roles (Warden/Administrator) can publish notices ---
    def test_ST_20_Notice__student_denied_access_to_notice_creation(self):
        """Student gets 403 trying to access notice management or creation."""
        self.client.login(username='stu1023', password='Pass@123')
        resp_add = self.client.get(reverse('notices:add'))
        self.assertEqual(resp_add.status_code, 403)

        resp_manage = self.client.get(reverse('notices:manage'))
        self.assertEqual(resp_manage.status_code, 403)
