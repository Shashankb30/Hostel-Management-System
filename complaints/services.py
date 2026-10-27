"""Business rules for Complaint Management (FR-06). Views call these functions only.

    submit_complaint      FR-06.01, .02   student raises a complaint (UT_16_Comp, UT_17_Comp)
    log_misconduct        FR-06.03, .06   staff logs a case; demerit points follow the severity (IT_16_Comp)
    list_complaints       FR-06.04        filter by status / category (UT_18_Comp)
    update_rules          FR-06.05        severity -> demerit points table
    demerit_total         FR-06.07        cumulative points per student (IT_18_Comp)
    change_status         FR-06.08, .09   Open / Under Review / Resolved with remarks, student notified (IT_17_Comp)
    escalate              FR-06.10        repeated or severe cases go to the administrator
    edit_complaint        FR-06.11        a resolved complaint is locked until reopened (ST_12_Comp)
    reopen                FR-06.11
    student_complaints    FR-06.12        a student's own complaints and demerit points
    category_summary      FR-06.13        counts by category (ST_11_Comp)
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from core.error_messages import msg
from core.models import Complaint, ComplaintUpdate, DemeritRecord, DemeritRule, UserAccount
from core.notifications import notify
from core.validators import ErrorCollector, RequiredValidator

DESCRIPTION_MAX = 2000
TITLE_MAX = Complaint._meta.get_field('title').max_length
REMARKS_MAX = 1000
RULE_POINTS_MAX = 100

# Escalation thresholds (FR-06.10). A case goes to the administrator when it is Major,
# when a student has this many misconduct cases, or when their demerit total reaches this.
ESCALATE_AFTER_CASES = 3
ESCALATE_AT_POINTS = 10

DEFAULT_RULES = [
    ('minor', 1, 'Minor breach of hostel rules'),
    ('moderate', 3, 'Repeated or disruptive breach of hostel rules'),
    ('major', 5, 'Serious misconduct'),
]

CATEGORIES = [value for value, _label in Complaint.CATEGORY_CHOICES]
SEVERITIES = [value for value, _label in Complaint.SEVERITY_CHOICES]
STATUSES = [value for value, _label in Complaint.STATUS_CHOICES]
STATUS_LABELS = dict(Complaint.STATUS_CHOICES)
CATEGORY_LABELS = dict(Complaint.CATEGORY_CHOICES)
SEVERITY_LABELS = dict(Complaint.SEVERITY_CHOICES)

# Moves allowed by change_status. A resolved complaint only leaves through reopen().
ALLOWED_MOVES = {
    Complaint.STATUS_OPEN: {Complaint.STATUS_UNDER_REVIEW, Complaint.STATUS_RESOLVED},
    Complaint.STATUS_UNDER_REVIEW: {Complaint.STATUS_OPEN, Complaint.STATUS_RESOLVED},
}


# --- small helpers -----------------------------------------------------------------------

def _clean(value):
    return value.strip() if isinstance(value, str) else value


def _short(text, limit=255):
    """Notification messages are limited to 255 characters."""
    return text if len(text) <= limit else text[:limit - 3].rstrip() + '...'


def _check_choice(value, allowed, label):
    if value not in allowed:
        raise ValidationError(msg('invalid_choice', field=label), code='invalid_choice')


def _check_max(value, limit, label):
    if len(value) > limit:
        raise ValidationError(msg('max_length', field=label, limit=limit), code='max_length')


def _notify(complaint, text):
    notify(complaint.student, 'COMPLAINT', _short(text))


def _record(complaint, old_status, new_status, remarks, by):
    return ComplaintUpdate.objects.create(
        complaint=complaint, old_status=old_status, new_status=new_status,
        remarks=remarks or '', changed_by=by)


def _title_from(description, title=''):
    title = _clean(title)
    if title:
        return title
    first_line = description.splitlines()[0].strip() if description else ''
    return first_line[:80]


# --- demerit rules (FR-06.05) ------------------------------------------------------------

def ensure_default_rules():
    """Create the default Minor / Moderate / Major rules if they are missing."""
    for severity, points, description in DEFAULT_RULES:
        DemeritRule.objects.get_or_create(
            severity=severity, defaults={'points': points, 'description': description})


def list_rules():
    ensure_default_rules()
    order = {severity: i for i, severity in enumerate(SEVERITIES)}
    return sorted(DemeritRule.objects.all(), key=lambda rule: order.get(rule.severity, 99))


def update_rules(points_by_severity):
    """Save the demerit points for each severity, e.g. {'minor': 1, 'major': 8}.

    Existing demerit records keep the points they were given, so editing a rule never
    rewrites history.
    """
    ensure_default_rules()
    errors = ErrorCollector()
    cleaned = {}
    for severity, raw in points_by_severity.items():
        label = f'{SEVERITY_LABELS.get(severity, severity)} points'
        try:
            _check_choice(severity, SEVERITIES, 'Severity')
            raw = str(raw).strip()
            if not raw:
                raise ValidationError(msg('required', field=label), code='required')
            try:
                points = int(raw)
            except ValueError:
                raise ValidationError(msg('integer', field=label), code='integer') from None
            if points < 0:
                raise ValidationError(msg('min_value', field=label, limit=0), code='min_value')
            if points > RULE_POINTS_MAX:
                raise ValidationError(msg('max_value', field=label, limit=RULE_POINTS_MAX), code='max_value')
            cleaned[severity] = points
        except ValidationError as exc:
            errors.add(severity, exc)
    errors.raise_if_any()
    with transaction.atomic():
        for severity, points in cleaned.items():
            DemeritRule.objects.filter(severity=severity).update(points=points)
    return list_rules()


# --- submit a complaint (FR-06.01, FR-06.02) ----------------------------------------------

def submit_complaint(student, category, description, title='', raised_by=None):
    """A student raises a complaint. It starts as Open and gets a unique ID (UT_16_Comp)."""
    category, description, title = _clean(category), _clean(description), _clean(title)
    errors = ErrorCollector()
    errors.check('category', RequiredValidator('Category'), category)
    if category:
        errors.check('category', _check_choice, category, CATEGORIES, 'Category')
    errors.check('description', RequiredValidator('Description'), description)   # UT_17_Comp
    if description:
        errors.check('description', _check_max, description, DESCRIPTION_MAX, 'Description')
    if title:
        errors.check('title', _check_max, title, TITLE_MAX, 'Title')
    errors.raise_if_any()

    with transaction.atomic():
        complaint = Complaint.objects.create(
            student=student, hostel=student.hostel, kind=Complaint.KIND_COMPLAINT,
            category=category, title=_title_from(description, title), description=description,
            status=Complaint.STATUS_OPEN, raised_by=raised_by or student.user_account)
        _record(complaint, '', Complaint.STATUS_OPEN, 'Complaint submitted', complaint.raised_by)
        _escalate_if_repeated_complaint(complaint)
    return complaint


# --- log a misconduct case (FR-06.03, FR-06.06, FR-06.07) ----------------------------------

def log_misconduct(student, severity, description, logged_by, category='discipline', title=''):
    """Warden or administrator logs a case. Demerit points come from the severity rule (IT_16_Comp)."""
    severity, description, title = _clean(severity), _clean(description), _clean(title)
    category = _clean(category) or 'discipline'
    errors = ErrorCollector()
    errors.check('severity', RequiredValidator('Severity'), severity)
    if severity:
        errors.check('severity', _check_choice, severity, SEVERITIES, 'Severity')
    errors.check('category', _check_choice, category, CATEGORIES, 'Category')
    errors.check('description', RequiredValidator('Description'), description)
    if description:
        errors.check('description', _check_max, description, DESCRIPTION_MAX, 'Description')
    if title:
        errors.check('title', _check_max, title, TITLE_MAX, 'Title')
    errors.raise_if_any()

    ensure_default_rules()
    rule = DemeritRule.objects.get(severity=severity)

    with transaction.atomic():
        complaint = Complaint.objects.create(
            student=student, hostel=student.hostel, kind=Complaint.KIND_MISCONDUCT,
            category=category, title=_title_from(description, title), description=description,
            severity=severity, status=Complaint.STATUS_OPEN, raised_by=logged_by)
        _record(complaint, '', Complaint.STATUS_OPEN, 'Misconduct case logged', logged_by)
        if rule.points > 0:
            DemeritRecord.objects.create(
                student=student, complaint=complaint, points=rule.points,
                reason=f'{SEVERITY_LABELS[severity]} misconduct: {complaint.title}'[:240],
                awarded_by=logged_by, awarded_on=timezone.localdate())
        total = demerit_total(student)
        _notify(complaint, (
            f'A misconduct case {complaint.complaint_id} was logged ({SEVERITY_LABELS[severity]}): '
            f'{rule.points} demerit point(s) added. Your total is {total}.'))
        _escalate_if_needed(complaint, total)
    return complaint


def demerit_total(student):
    """Cumulative demerit points for a student (IT_18_Comp)."""
    return DemeritRecord.objects.filter(student=student).aggregate(total=Sum('points'))['total'] or 0


def demerit_history(student):
    return (DemeritRecord.objects.filter(student=student)
            .select_related('complaint').order_by('-awarded_on', '-id'))


# --- status, reopen, edit lock (FR-06.08, FR-06.09, FR-06.11) ------------------------------

def change_status(complaint, new_status, remarks, by):
    """Move a complaint between Open, Under Review and Resolved, with remarks (IT_17_Comp)."""
    new_status, remarks = _clean(new_status), _clean(remarks)
    errors = ErrorCollector()
    errors.check('status', RequiredValidator('Status'), new_status)
    if new_status:
        errors.check('status', _check_choice, new_status, STATUSES, 'Status')
    if new_status == Complaint.STATUS_RESOLVED:
        errors.check('remarks', RequiredValidator('Remarks'), remarks)
    if remarks:
        errors.check('remarks', _check_max, remarks, REMARKS_MAX, 'Remarks')
    errors.raise_if_any()

    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        if complaint.status == Complaint.STATUS_RESOLVED:
            raise ValidationError(msg('complaint_locked'), code='complaint_locked')
        if new_status not in ALLOWED_MOVES.get(complaint.status, set()):
            raise ValidationError(
                msg('invalid_status_change', old=STATUS_LABELS[complaint.status], new=STATUS_LABELS[new_status]),
                code='invalid_status_change')
        old_status = complaint.status
        complaint.status = new_status
        complaint.remarks = remarks or complaint.remarks
        if new_status == Complaint.STATUS_RESOLVED:
            complaint.resolved_by = by
            complaint.resolved_at = timezone.now()
        complaint.save()
        _record(complaint, old_status, new_status, remarks, by)
        text = f'Your complaint {complaint.complaint_id} is now {STATUS_LABELS[new_status]}.'
        if remarks:
            text += f' Remarks: {remarks}'
        _notify(complaint, text)
    return complaint


def reopen(complaint, remarks, by):
    """Reopen a resolved complaint so it can be worked on or edited again (ST_12_Comp)."""
    remarks = _clean(remarks)
    errors = ErrorCollector()
    errors.check('remarks', RequiredValidator('Remarks'), remarks)
    if remarks:
        errors.check('remarks', _check_max, remarks, REMARKS_MAX, 'Remarks')
    errors.raise_if_any()

    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        if complaint.status != Complaint.STATUS_RESOLVED:
            raise ValidationError(msg('complaint_not_resolved'), code='complaint_not_resolved')
        complaint.status = Complaint.STATUS_OPEN
        complaint.remarks = remarks
        complaint.resolved_by = None
        complaint.resolved_at = None
        complaint.save()
        _record(complaint, Complaint.STATUS_RESOLVED, Complaint.STATUS_OPEN, remarks, by)
        _notify(complaint, f'Your complaint {complaint.complaint_id} was reopened. Remarks: {remarks}')
    return complaint


def edit_complaint(complaint, description, category=None, title=None):
    """Change a complaint's text. A resolved complaint is locked until it is reopened (ST_12_Comp)."""
    description = _clean(description)
    category = _clean(category) if category is not None else complaint.category
    title = _clean(title) if title is not None else ''
    errors = ErrorCollector()
    errors.check('description', RequiredValidator('Description'), description)
    if description:
        errors.check('description', _check_max, description, DESCRIPTION_MAX, 'Description')
    errors.check('category', _check_choice, category, CATEGORIES, 'Category')
    if title:
        errors.check('title', _check_max, title, TITLE_MAX, 'Title')
    errors.raise_if_any()

    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        if complaint.status == Complaint.STATUS_RESOLVED:
            raise ValidationError(msg('complaint_locked'), code='complaint_locked')
        complaint.description = description
        complaint.category = category
        complaint.title = _title_from(description, title)
        complaint.save()
    return complaint


# --- escalation (FR-06.10) ---------------------------------------------------------------

def escalate(complaint, reason, by=None):
    """Send a complaint to the administrator, who is notified."""
    reason = _clean(reason)
    errors = ErrorCollector()
    errors.check('reason', RequiredValidator('Reason'), reason)
    if reason:
        errors.check('reason', _check_max, reason, Complaint._meta.get_field('escalation_reason').max_length, 'Reason')
    errors.raise_if_any()

    with transaction.atomic():
        complaint = Complaint.objects.select_for_update().get(pk=complaint.pk)
        if complaint.is_escalated:
            raise ValidationError(msg('already_escalated'), code='already_escalated')
        complaint.is_escalated = True
        complaint.escalation_reason = reason
        complaint.save()
        _record(complaint, complaint.status, complaint.status, f'Escalated to the administrator: {reason}', by)
        for admin in UserAccount.objects.filter(role=UserAccount.ROLE_ADMIN, is_locked=False, user__is_active=True):
            notify(admin, 'COMPLAINT', _short(f'{complaint.complaint_id} escalated: {reason}'))
    return complaint


def _escalate_if_needed(complaint, total):
    """Automatic escalation for a new misconduct case: Major, repeated, or too many points."""
    reasons = []
    if complaint.severity == 'major':
        reasons.append('Major misconduct')
    cases = Complaint.objects.filter(student=complaint.student, kind=Complaint.KIND_MISCONDUCT).count()
    if cases >= ESCALATE_AFTER_CASES:
        reasons.append(f'Repeated misconduct ({cases} cases)')
    if total >= ESCALATE_AT_POINTS:
        reasons.append(f'Demerit total reached {total}')
    if reasons:
        escalate(complaint, '; '.join(reasons))


def _escalate_if_repeated_complaint(complaint):
    """A student keeps raising the same kind of complaint: tell the administrator."""
    unresolved = (Complaint.objects
                  .filter(student=complaint.student, kind=Complaint.KIND_COMPLAINT, category=complaint.category)
                  .exclude(status=Complaint.STATUS_RESOLVED).count())
    if unresolved >= ESCALATE_AFTER_CASES:
        escalate(complaint, f'Repeated {CATEGORY_LABELS[complaint.category].lower()} complaint '
                            f'({unresolved} unresolved)')


# --- viewing and reporting (FR-06.04, FR-06.12, FR-06.13) ----------------------------------

def _scope(account, queryset):
    """Staff see their own hostel's complaints (every hostel if the account has none)."""
    if account is not None and account.hostel_id is not None:
        return queryset.filter(hostel_id=account.hostel_id)
    return queryset


def list_complaints(account, status='', category='', kind='', escalated=False, search=''):
    """Complaints for staff screens, newest first. Unknown filter values are ignored (UT_18_Comp)."""
    complaints = _scope(account, Complaint.objects.select_related('student', 'resolved_by__user'))
    if status in STATUSES:
        complaints = complaints.filter(status=status)
    if category in CATEGORIES:
        complaints = complaints.filter(category=category)
    if kind in (Complaint.KIND_COMPLAINT, Complaint.KIND_MISCONDUCT):
        complaints = complaints.filter(kind=kind)
    if escalated:
        complaints = complaints.filter(is_escalated=True)
    search = _clean(search)
    if search:
        complaints = complaints.filter(
            Q(student__full_name__icontains=search) | Q(student__roll_no__icontains=search)
            | Q(title__icontains=search) | Q(description__icontains=search))
    return complaints


def student_complaints(student):
    """The complaints a student raised themselves (FR-06.12)."""
    return Complaint.objects.filter(student=student, kind=Complaint.KIND_COMPLAINT)


def category_summary(account, start=None, end=None):
    """Complaint counts grouped by category and status (ST_11_Comp)."""
    complaints = _scope(account, Complaint.objects.all())
    if start is not None:
        complaints = complaints.filter(created_at__date__gte=start)
    if end is not None:
        complaints = complaints.filter(created_at__date__lte=end)
    counts = {row['category']: row for row in complaints.values('category').annotate(
        total=Count('id'),
        open=Count('id', filter=Q(status=Complaint.STATUS_OPEN)),
        under_review=Count('id', filter=Q(status=Complaint.STATUS_UNDER_REVIEW)),
        resolved=Count('id', filter=Q(status=Complaint.STATUS_RESOLVED)))}
    rows, totals = [], {'total': 0, 'open': 0, 'under_review': 0, 'resolved': 0}
    for value, label in Complaint.CATEGORY_CHOICES:
        row = counts.get(value, {})
        entry = {'category': value, 'label': label}
        for key in totals:
            entry[key] = row.get(key, 0)
            totals[key] += entry[key]
        rows.append(entry)
    return {'rows': rows, 'totals': totals}
