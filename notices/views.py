"""Views for Notice / Information Management (FR-10)."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.feedback import flash_errors
from core.models import Notice, UserAccount
from core.roles import get_account, get_role, role_required

from . import services
from .forms import NoticeFilterForm, NoticeForm

STAFF_ONLY = role_required(UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)
AUTHENTICATED = role_required(UserAccount.ROLE_STUDENT, UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN)

PAGE_SIZE = 25


def _scope_hostel(account):
    """Return hostel for wardens, None for admins (access to all notices)."""
    if account and account.role == UserAccount.ROLE_WARDEN:
        return account.hostel
    return None


# --- Student Notice Board (FR-10.03, FR-10.10) ---

@AUTHENTICATED
def board(request):
    """Notice board visible to students, wardens and admins (FR-10.10)."""
    account = get_account(request.user)
    role = get_role(request.user)
    hostel = account.hostel if account else None

    form = NoticeFilterForm(request.GET)
    q = request.GET.get('q', '').strip()
    audience_filter = request.GET.get('audience', '').strip()

    notices = services.get_active_notices(role=role, hostel=hostel)
    if q:
        notices = notices.filter(title__icontains=q) | notices.filter(body__icontains=q)
    if audience_filter:
        notices = notices.filter(audience=audience_filter)

    page = Paginator(notices, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'notices/board.html', {
        'page': page,
        'filter_form': form,
        'q': q,
        'selected_audience': audience_filter,
        'is_staff': role in (UserAccount.ROLE_WARDEN, UserAccount.ROLE_ADMIN),
    })


# --- Staff Notice Management (Warden / Admin) ---

@STAFF_ONLY
def manage_notices(request):
    """List, search and manage notices (FR-10.07, FR-10.08, ST_19)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    form = NoticeFilterForm(request.GET)
    q = request.GET.get('q', '').strip()
    audience_filter = request.GET.get('audience', '').strip()

    notices = services.search_notices(
        keyword=q,
        audience=audience_filter,
        hostel=hostel,
        include_unpublished=True,
    )
    page = Paginator(notices, PAGE_SIZE).get_page(request.GET.get('page'))

    return render(request, 'notices/manage.html', {
        'page': page,
        'filter_form': form,
        'q': q,
        'selected_audience': audience_filter,
    })


@STAFF_ONLY
def notice_add(request):
    """Create and publish a new notice (FR-10.01, FR-10.02, FR-10.04, UT_28, UT_29)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            try:
                notice = services.publish_notice(
                    title=form.cleaned_data['title'],
                    body=form.cleaned_data['body'],
                    author=account,
                    audience=form.cleaned_data['audience'],
                    hostel=hostel,
                    expires_at=form.cleaned_data.get('expires_at'),
                    is_published=form.cleaned_data.get('is_published', True),
                )
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                messages.success(request, f'Notice "{notice.title}" created successfully.')
                return redirect('notices:manage')
    else:
        form = NoticeForm(initial={'is_published': True})

    return render(request, 'notices/form.html', {
        'form': form,
        'title': 'Create Notice',
    })


@STAFF_ONLY
def notice_edit(request, pk):
    """Edit an existing notice (FR-10.05, IT_28)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    qs = Notice.objects.all()
    if hostel:
        qs = qs.filter(Q(hostel__isnull=True) | Q(hostel=hostel))
    notice = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            try:
                services.update_notice(
                    notice=notice,
                    title=form.cleaned_data['title'],
                    body=form.cleaned_data['body'],
                    audience=form.cleaned_data['audience'],
                    expires_at=form.cleaned_data.get('expires_at'),
                    is_published=form.cleaned_data.get('is_published', True),
                )
            except ValidationError as exc:
                flash_errors(request, exc)
            else:
                messages.success(request, f'Notice "{notice.title}" updated successfully.')
                return redirect('notices:manage')
    else:
        initial = {}
        if notice.expires_at:
            initial['expires_at'] = notice.expires_at.date()
        form = NoticeForm(instance=notice, initial=initial)

    return render(request, 'notices/form.html', {
        'form': form,
        'title': f'Edit Notice: {notice.title}',
        'notice': notice,
    })


@STAFF_ONLY
@require_POST
def notice_delete(request, pk):
    """Delete a notice (FR-10.06, IT_29)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    qs = Notice.objects.all()
    if hostel:
        qs = qs.filter(Q(hostel__isnull=True) | Q(hostel=hostel))
    notice = get_object_or_404(qs, pk=pk)

    title = notice.title
    services.delete_notice(notice)
    messages.success(request, f'Notice "{title}" was deleted.')
    return redirect('notices:manage')


@STAFF_ONLY
@require_POST
def notice_expire(request, pk):
    """Expire or unpublish a notice (FR-10.06, IT_29)."""
    account = get_account(request.user)
    hostel = _scope_hostel(account)

    qs = Notice.objects.all()
    if hostel:
        qs = qs.filter(Q(hostel__isnull=True) | Q(hostel=hostel))
    notice = get_object_or_404(qs, pk=pk)

    services.expire_notice(notice)
    messages.success(request, 'The notice was marked as expired.')
    return redirect('notices:manage')
