"""Student Management screens (FR-02). Administrators only."""
from django.core.paginator import Paginator
from django.shortcuts import render

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
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add New Student'})
