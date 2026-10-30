"""Versioned relational schema for HMS. Business rules belong in module services."""
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Hostel(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name


class UserAccount(TimeStampedModel):
    ROLE_STUDENT = 'student'; ROLE_WARDEN = 'warden'; ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [(ROLE_STUDENT, 'Student'), (ROLE_WARDEN, 'Warden'), (ROLE_ADMIN, 'Administrator')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hms_account')
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_STUDENT, db_index=True)
    hostel = models.ForeignKey(Hostel, null=True, blank=True, on_delete=models.PROTECT, related_name='accounts')
    phone = models.CharField(max_length=20, blank=True)
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    def __str__(self): return self.user.get_username()


class Student(TimeStampedModel):
    user_account = models.OneToOneField(UserAccount, on_delete=models.PROTECT, related_name='student')
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='students')
    roll_no = models.CharField(max_length=32, unique=True)
    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    course = models.CharField(max_length=100, blank=True)
    year_of_study = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    guardian_name = models.CharField(max_length=160, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f'{self.roll_no} - {self.full_name}'
    @property
    def student_id(self):
        """The unique Student ID people see, for example STU00012.

        Built from the primary key, so two students can never share one and it never changes.
        """
        return f'STU{self.pk:05d}' if self.pk is not None else ''


class Room(TimeStampedModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='rooms')
    room_no = models.CharField(max_length=20)
    block = models.CharField(max_length=40, blank=True)
    floor = models.SmallIntegerField(default=0)
    room_type = models.CharField(max_length=40, blank=True)
    capacity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['hostel', 'room_no'], name='uq_room_hostel_roomno'), models.CheckConstraint(condition=Q(capacity__gte=1), name='ck_room_capacity_positive')]
        indexes = [models.Index(fields=['hostel', 'is_active'], name='ix_room_hostel_active')]
    @property
    def occupancy(self): return self.allocations.filter(status=Allocation.STATUS_ACTIVE).count()
    @property
    def vacancies(self): return max(self.capacity - self.occupancy, 0)
    def __str__(self): return f'{self.hostel.code}/{self.room_no}'


class Allocation(TimeStampedModel):
    STATUS_ACTIVE = 'active'; STATUS_ENDED = 'ended'; STATUS_TRANSFERRED = 'transferred'
    STATUS_CHOICES = [(STATUS_ACTIVE, 'Active'), (STATUS_ENDED, 'Ended'), (STATUS_TRANSFERRED, 'Transferred')]
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='allocations')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='allocations')
    allocated_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='allocations_made')
    allocated_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student'], condition=Q(status='active'), name='uq_student_active_allocation'), models.CheckConstraint(condition=Q(ended_on__isnull=True) | Q(ended_on__gte=models.F('allocated_on')), name='ck_allocation_dates')]
        indexes = [models.Index(fields=['room', 'status'], name='ix_allocation_room_status')]


class AllocationRequest(TimeStampedModel):
    STATUS_WAITING = 'waiting'; STATUS_APPROVED = 'approved'; STATUS_REJECTED = 'rejected'; STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [(STATUS_WAITING, 'Waiting'), (STATUS_APPROVED, 'Approved'), (STATUS_REJECTED, 'Rejected'), (STATUS_CANCELLED, 'Cancelled')]
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='allocation_requests')
    preferred_hostel = models.ForeignKey(Hostel, null=True, blank=True, on_delete=models.PROTECT, related_name='allocation_requests')
    requested_room_type = models.CharField(max_length=40, blank=True)
    priority = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_WAITING, db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='allocation_requests_processed')
    class Meta:
        indexes = [models.Index(fields=['status', '-priority', 'requested_at'], name='ix_allocreq_queue')]


class AllocationRule(TimeStampedModel):
    """A configurable room-allocation priority rule (Issue #55, FR-04.03).

    A student's priority score is the sum of ``weight x value`` over every active rule.
    Higher scores are served first; students with equal scores are served first-come,
    first-served. See allocation.services.priority_score().
    """
    CRITERION_SENIORITY = 'seniority'
    CRITERION_CHOICES = [(CRITERION_SENIORITY, 'Seniority (year of study)')]
    criterion = models.CharField(max_length=20, choices=CRITERION_CHOICES, unique=True)
    weight = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=240, blank=True)

    def __str__(self): return f'{self.get_criterion_display()} (weight {self.weight})'


class FeeRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='fee_records')
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='fee_records')
    academic_year = models.CharField(max_length=9)
    description = models.CharField(max_length=160, default='Hostel fee')
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    due_date = models.DateField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'academic_year', 'description'], name='uq_fee_student_year_desc'), models.CheckConstraint(condition=Q(amount_due__gte=0), name='ck_fee_due_nonnegative')]
    @property
    def amount_paid(self): return self.payments.aggregate(total=models.Sum('amount'))['total'] or 0
    @property
    def balance(self): return max(self.amount_due - self.amount_paid, 0)
    @property
    def fee_status(self):
        if self.amount_paid <= 0: return 'unpaid'
        return 'paid' if self.balance == 0 else 'partially_paid'


class Payment(TimeStampedModel):
    MODE_CHOICES = [('cash', 'Cash'), ('online', 'Online'), ('card', 'Card'), ('bank_transfer', 'Bank transfer')]
    fee_record = models.ForeignKey(FeeRecord, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    paid_on = models.DateField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='payments_received')
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name='ck_payment_amount_positive')]
        indexes = [models.Index(fields=['paid_on'], name='ix_payment_paid_on')]


class Complaint(TimeStampedModel):
    """A student complaint (FR-06.01) or a misconduct case logged by staff (FR-06.03).

    ``student`` is the student concerned: the person who complained, or, for a misconduct
    case, the person it is about. Demerit points only ever attach to misconduct cases.
    """
    KIND_COMPLAINT = 'complaint'
    KIND_MISCONDUCT = 'misconduct'
    KIND_CHOICES = [(KIND_COMPLAINT, 'Complaint'), (KIND_MISCONDUCT, 'Misconduct case')]

    CATEGORY_CHOICES = [('maintenance', 'Maintenance'), ('discipline', 'Discipline'),
                        ('food', 'Food'), ('other', 'Other')]

    STATUS_OPEN = 'open'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = [(STATUS_OPEN, 'Open'), (STATUS_UNDER_REVIEW, 'Under Review'),
                      (STATUS_RESOLVED, 'Resolved')]

    SEVERITY_CHOICES = [('minor', 'Minor'), ('moderate', 'Moderate'), ('major', 'Major')]

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='complaints')
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='complaints')
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default=KIND_COMPLAINT, db_index=True)
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES, default='other', db_index=True)
    title = models.CharField(max_length=160)
    description = models.TextField()
    severity = models.CharField(max_length=12, choices=SEVERITY_CHOICES, blank=True, default='')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    remarks = models.TextField(blank=True)
    raised_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='complaints_raised')
    is_escalated = models.BooleanField(default=False, db_index=True)
    escalation_reason = models.CharField(max_length=240, blank=True)
    resolved_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='complaints_resolved')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.CheckConstraint(condition=~Q(description=''), name='ck_complaint_description_not_blank'),
        ]

    def __str__(self): return f'#{self.pk} {self.title}'

    @property
    def complaint_id(self):
        """The unique complaint ID people see, for example CMP00012 (UT_16_Comp)."""
        return f'CMP{self.pk:05d}' if self.pk is not None else ''


class DemeritRule(TimeStampedModel):
    """Points awarded for each misconduct severity (FR-06.05). Editable by staff."""
    severity = models.CharField(max_length=12, choices=Complaint.SEVERITY_CHOICES, unique=True)
    points = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['points', 'id']

    def __str__(self): return f'{self.get_severity_display()}: {self.points} point(s)'


class ComplaintUpdate(TimeStampedModel):
    """One entry in a complaint's history: every status change with its remarks (FR-06.08)."""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='updates')
    old_status = models.CharField(max_length=16, blank=True, choices=Complaint.STATUS_CHOICES)
    new_status = models.CharField(max_length=16, choices=Complaint.STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    changed_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='complaint_updates')

    class Meta:
        ordering = ['created_at', 'id']


class DemeritRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='demerit_records')
    complaint = models.ForeignKey(Complaint, null=True, blank=True, on_delete=models.SET_NULL, related_name='demerit_records')
    points = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    reason = models.CharField(max_length=240)
    awarded_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='demerits_awarded')
    awarded_on = models.DateField()
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(points__gte=1), name='ck_demerit_points_positive')]
    @property
    def student_total(self): return self.student.demerit_records.aggregate(total=models.Sum('points'))['total'] or 0


class AttendanceRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='attendance_records')
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='attendance_records')
    attendance_date = models.DateField()
    check_in_at = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='attendance_recorded')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'attendance_date'], name='uq_attendance_student_date'), models.CheckConstraint(condition=Q(check_out_at__isnull=True) | Q(check_in_at__isnull=False), name='ck_checkout_requires_checkin'), models.CheckConstraint(condition=Q(check_out_at__isnull=True) | Q(check_out_at__gte=models.F('check_in_at')), name='ck_attendance_time_order')]
        indexes = [models.Index(fields=['hostel', 'attendance_date'], name='ix_attendance_hostel_day')]


class VisitorLog(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='visitor_logs')
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='visitor_logs')
    visitor_name = models.CharField(max_length=160)
    visitor_phone = models.CharField(max_length=20, blank=True)
    id_proof = models.CharField(max_length=50, blank=True, default='')
    purpose = models.CharField(max_length=240, blank=True)
    checked_in_at = models.DateTimeField()
    checked_out_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='visitors_recorded')
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(checked_out_at__isnull=True) | Q(checked_out_at__gte=models.F('checked_in_at')), name='ck_visitor_time_order')]

    def __str__(self):
        return f'{self.visitor_name} -> {self.student.full_name}'

    @property
    def duration(self):
        """Return the visit duration as timedelta, or None if still active."""
        if not self.checked_in_at or not self.checked_out_at:
            return None
        return self.checked_out_at - self.checked_in_at

    @property
    def is_active(self):
        """Return True if visitor is currently checked in and not checked out."""
        return self.checked_out_at is None


class LeaveApplication(TimeStampedModel):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')]
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='leave_applications')
    hostel = models.ForeignKey(Hostel, on_delete=models.PROTECT, related_name='leave_applications')
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()
    destination = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    reviewed_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='leave_applications_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(to_date__gte=models.F('from_date')), name='ck_leave_date_order')]


class Notice(TimeStampedModel):
    AUDIENCE_CHOICES = [('all', 'All'), ('students', 'Students'), ('wardens', 'Wardens')]
    hostel = models.ForeignKey(Hostel, null=True, blank=True, on_delete=models.PROTECT, related_name='notices')
    title = models.CharField(max_length=160)
    body = models.TextField()
    audience = models.CharField(max_length=16, choices=AUDIENCE_CHOICES, default='all', db_index=True)
    published_by = models.ForeignKey(UserAccount, null=True, blank=True, on_delete=models.SET_NULL, related_name='notices_published')
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    class Meta:
        indexes = [models.Index(fields=['is_published', 'expires_at'], name='ix_notice_published_expiry')]


class Notification(TimeStampedModel):
    """In-app message for a user. Created by core.notifications.notify() (Issue #14)."""
    CATEGORY_ALLOCATION = 'ALLOCATION'
    CATEGORY_FEE = 'FEE'
    CATEGORY_LEAVE = 'LEAVE'
    CATEGORY_COMPLAINT = 'COMPLAINT'
    CATEGORY_NOTICE = 'NOTICE'
    CATEGORY_CHOICES = [
        (CATEGORY_ALLOCATION, 'Allocation'),
        (CATEGORY_FEE, 'Fee'),
        (CATEGORY_LEAVE, 'Leave'),
        (CATEGORY_COMPLAINT, 'Complaint'),
        (CATEGORY_NOTICE, 'Notice'),
    ]
    recipient = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='notifications')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['recipient', 'is_read'], name='ix_notification_unread')]

    def __str__(self):
        return f'{self.category}: {self.message[:40]}'
