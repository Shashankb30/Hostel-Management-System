"""Business rules for Leave Management (FR-09).

    submit_leave_application       FR-09.01, .02, .03   Submit leave with valid dates and reason (UT_25, UT_26, UT_27)
    approve_application            FR-09.05             Approve pending application and notify student (IT_25)
    reject_application             FR-09.06             Reject pending application with remarks and notify student (IT_26)
    request_more_information       FR-09.08             Request more information from student and notify (FR-09.08)
    resubmit_application          FR-09.08             Student updates application when more info requested
    get_overlapping_leaves         FR-09.07             Flag overlapping leave dates with approved leaves (IT_27)
    get_student_leaves             FR-09.09             Student leave application history (ST_17)
    get_all_leaves                 FR-09.10             Admin/warden consolidated leave records (ST_18)
"""
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from core.error_messages import msg
from core.models import LeaveApplication, Notification
from core.notifications import notify


def submit_leave_application(student, from_date, to_date, reason, destination=''):
    """Student submits a leave application (FR-09.01, FR-09.02, FR-09.03)."""
    if not student:
        raise ValidationError(msg('required', field='Student'), code='required')

    reason = (reason or '').strip()
    if not reason:
        raise ValidationError(msg('required', field='Reason'), code='required')

    if not from_date:
        raise ValidationError(msg('required', field='From date'), code='required')
    if not to_date:
        raise ValidationError(msg('required', field='To date'), code='required')

    if to_date < from_date:
        raise ValidationError(msg('date_range', start='From date', end='To date'), code='date_range')

    application = LeaveApplication.objects.create(
        student=student,
        hostel=student.hostel,
        from_date=from_date,
        to_date=to_date,
        reason=reason,
        destination=(destination or '').strip(),
        status=LeaveApplication.STATUS_PENDING,
    )
    return application


def get_overlapping_leaves(application):
    """Find approved leave applications for the same student overlapping the given dates (FR-09.07, IT_27).

    Two date ranges [from_date, to_date] and [A, B] overlap if:
        A <= to_date AND B >= from_date
    """
    return LeaveApplication.objects.filter(
        student=application.student,
        status=LeaveApplication.STATUS_APPROVED,
        from_date__lte=application.to_date,
        to_date__gte=application.from_date,
    ).exclude(pk=application.pk)


def approve_application(application, reviewer, remarks=''):
    """Warden or admin approves a pending or info_requested application (FR-09.05, IT_25)."""
    if application.status not in (LeaveApplication.STATUS_PENDING, LeaveApplication.STATUS_INFO_REQUESTED):
        raise ValidationError('Only pending or info-requested applications can be approved.')

    application.status = LeaveApplication.STATUS_APPROVED
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    if remarks:
        application.reviewer_remarks = remarks.strip()
    application.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_remarks', 'updated_at'])

    notify(
        student=application.student,
        category=Notification.CATEGORY_LEAVE,
        message=f'Your leave application {application.application_id} was approved',
    )
    return application


def reject_application(application, reviewer, remarks):
    """Warden or admin rejects an application with mandatory remarks (FR-09.06, IT_26)."""
    remarks = (remarks or '').strip()
    if not remarks:
        raise ValidationError(msg('required', field='Rejection remarks'), code='required')

    if application.status not in (LeaveApplication.STATUS_PENDING, LeaveApplication.STATUS_INFO_REQUESTED):
        raise ValidationError('Only pending or info-requested applications can be rejected.')

    application.status = LeaveApplication.STATUS_REJECTED
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.reviewer_remarks = remarks
    application.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_remarks', 'updated_at'])

    notify(
        student=application.student,
        category=Notification.CATEGORY_LEAVE,
        message=f'Your leave application {application.application_id} was rejected: {remarks}',
    )
    return application


def request_more_information(application, reviewer, remarks):
    """Warden or admin requests additional information from the student (FR-09.08)."""
    remarks = (remarks or '').strip()
    if not remarks:
        raise ValidationError(msg('required', field='Remarks'), code='required')

    if application.status != LeaveApplication.STATUS_PENDING:
        raise ValidationError('Information can only be requested on pending applications.')

    application.status = LeaveApplication.STATUS_INFO_REQUESTED
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.reviewer_remarks = remarks
    application.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_remarks', 'updated_at'])

    notify(
        student=application.student,
        category=Notification.CATEGORY_LEAVE,
        message=f'More information requested for leave {application.application_id}: {remarks}',
    )
    return application


def resubmit_application(application, from_date=None, to_date=None, reason=None, destination=None):
    """Student updates and resubmits an application after information was requested (FR-09.08)."""
    if application.status != LeaveApplication.STATUS_INFO_REQUESTED:
        raise ValidationError('Only applications with status "More Info Requested" can be resubmitted.')

    if from_date is not None:
        application.from_date = from_date
    if to_date is not None:
        application.to_date = to_date
    if reason is not None:
        reason = reason.strip()
        if not reason:
            raise ValidationError(msg('required', field='Reason'), code='required')
        application.reason = reason
    if destination is not None:
        application.destination = destination.strip()

    if application.to_date < application.from_date:
        raise ValidationError(msg('date_range', start='From date', end='To date'), code='date_range')

    application.status = LeaveApplication.STATUS_PENDING
    application.save(update_fields=['from_date', 'to_date', 'reason', 'destination', 'status', 'updated_at'])
    return application


def cancel_application(application, student):
    """Student cancels their pending leave application."""
    if application.student != student:
        raise ValidationError('You cannot cancel another student\'s leave application.')
    if application.status not in (LeaveApplication.STATUS_PENDING, LeaveApplication.STATUS_INFO_REQUESTED):
        raise ValidationError('Only pending applications can be cancelled.')

    application.status = LeaveApplication.STATUS_CANCELLED
    application.save(update_fields=['status', 'updated_at'])
    return application


def get_student_leaves(student):
    """Student's leave application history (FR-09.09, ST_17)."""
    return LeaveApplication.objects.filter(student=student).select_related(
        'hostel', 'reviewed_by', 'reviewed_by__user'
    ).order_by('-created_at')


def get_all_leaves(hostel=None, status=None, query=None):
    """Consolidated leave records across students (FR-09.10, ST_18)."""
    qs = LeaveApplication.objects.select_related(
        'student', 'student__user_account', 'hostel', 'reviewed_by', 'reviewed_by__user'
    ).all()

    if hostel is not None:
        qs = qs.filter(hostel=hostel)

    if status:
        qs = qs.filter(status=status)

    if query:
        query = query.strip()
        qs = qs.filter(
            Q(student__full_name__icontains=query) |
            Q(student__roll_no__icontains=query) |
            Q(reason__icontains=query)
        )

    return qs.order_by('-created_at')
