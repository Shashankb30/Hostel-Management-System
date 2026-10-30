"""Administrator screens: Users & Roles (Issue #25, FR-01.10)."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.feedback import flash_errors
from core.models import UserAccount
from core.roles import role_required

from . import user_service
from .user_forms import UserCreateForm, UserEditForm

ROLE_VALUES = {value for value, _label in UserAccount.ROLE_CHOICES}
ADMIN_ONLY = role_required(UserAccount.ROLE_ADMIN)


@ADMIN_ONLY
def user_list(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    status = request.GET.get('status', '')
    accounts = UserAccount.objects.select_related('user', 'hostel').order_by('user__username')
    if query:
        accounts = accounts.filter(
            Q(user__username__icontains=query) | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query) | Q(user__email__icontains=query))
    if role in ROLE_VALUES:
        accounts = accounts.filter(role=role)
    if status == 'active':
        accounts = accounts.filter(user__is_active=True, is_locked=False)
    elif status == 'inactive':
        accounts = accounts.filter(user__is_active=False)
    elif status == 'locked':
        accounts = accounts.filter(is_locked=True)
    return render(request, 'accounts/user_list.html', {
        'accounts': accounts, 'query': query, 'role': role, 'status': status,
        'roles': UserAccount.ROLE_CHOICES,
    })


@ADMIN_ONLY
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        account = user_service.create_account(
            username=data['username'], password=data['password1'], role=data['role'],
            hostel=data['hostel'], first_name=data['first_name'], last_name=data['last_name'],
            email=data['email'], phone=data['phone'])
        messages.success(request, f'Account {account.user.username} created')
        return redirect('accounts:users')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Add user'})


@ADMIN_ONLY
def user_edit(request, pk):
    account = get_object_or_404(UserAccount.objects.select_related('user', 'hostel'), pk=pk)
    form = UserEditForm(request.POST or None, account=account, acting_user=request.user)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            user_service.update_account(
                account, acting_user=request.user, role=data['role'], hostel=data['hostel'],
                first_name=data['first_name'], last_name=data['last_name'],
                email=data['email'], phone=data['phone'])
        except ValidationError as exc:
            flash_errors(request, exc)
        else:
            messages.success(request, f'Account {account.user.username} updated')
            return redirect('accounts:users')
    return render(request, 'accounts/user_form.html', {
        'form': form, 'title': f'Edit {account.user.username}'})


def _account_action(request, pk, action, done):
    account = get_object_or_404(UserAccount.objects.select_related('user'), pk=pk)
    try:
        action(account)
    except ValidationError as exc:
        flash_errors(request, exc)
    else:
        messages.success(request, f'Account {account.user.username} {done}')
    return redirect('accounts:users')


@ADMIN_ONLY
@require_POST
def user_deactivate(request, pk):
    return _account_action(
        request, pk,
        lambda account: user_service.set_active(account, False, acting_user=request.user),
        'deactivated')


@ADMIN_ONLY
@require_POST
def user_reactivate(request, pk):
    return _account_action(
        request, pk,
        lambda account: user_service.set_active(account, True, acting_user=request.user),
        'reactivated')


@ADMIN_ONLY
@require_POST
def user_unlock(request, pk):
    return _account_action(request, pk, user_service.unlock, 'unlocked')
