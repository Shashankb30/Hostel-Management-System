"""Student Management screens (FR-02). Administrators only."""
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect

from . import services

from core.models import Student, UserAccount
from core.roles import get_account, role_required

from .forms import StudentRegistrationForm

PAGE_SIZE = 25
ADMIN_ONLY = role_required(UserAccount.ROLE_ADMIN)


@ADMIN_ONLY
def student_list(request):
    """Student Management: every registered student, with the Add New Student button."""
    students = Student.objects.select_related('hostel').order_by('roll_no')
    page = Paginator(students, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'students/student_list.html', {'page': page})


@ADMIN_ONLY
def student_add(request):
    """Add New Student (UC-02)."""
    account = get_account(request.user)
    form = StudentRegistrationForm(
        request.POST or None, initial={'hostel': account.hostel_id if account else None})
    if request.method == 'POST' and form.is_valid():
        result = services.register_student(**form.cleaned_data)
        _announce(request, result)
        return redirect('students:list')
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add New Student'})


def _announce(request, result):
    student = result.student
    messages.success(
        request, f'Student {student.full_name} registered. Student ID: {student.student_id}')
    messages.info(
        request,
        f'Login for {student.full_name}: username {result.username}, temporary password '
        f'{result.temporary_password}. Give it to the student now; it is not shown again.')
