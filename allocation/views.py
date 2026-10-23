"""Room Allocation screens. This batch adds only the student's own room page (FR-03.08);
FR-04 adds the allocation and transfer screens to this app."""
from django.shortcuts import render

from core.models import Allocation, Student, UserAccount
from core.roles import get_account, role_required

STUDENT_ONLY = role_required(UserAccount.ROLE_STUDENT)


@STUDENT_ONLY
def my_room(request):
    """My Room: the student's own room, read live from the room record."""
    student = Student.objects.filter(user_account=get_account(request.user)).first()
    allocation, roommates = None, 0
    if student is not None:
        allocation = (Allocation.objects.select_related('room__hostel')
                      .filter(student=student, status=Allocation.STATUS_ACTIVE).first())
    if allocation is not None:
        roommates = (Allocation.objects
                     .filter(room=allocation.room, status=Allocation.STATUS_ACTIVE)
                     .exclude(pk=allocation.pk).count())
    return render(request, 'allocation/my_room.html', {
        'student': student, 'allocation': allocation,
        'room': allocation.room if allocation else None, 'roommates': roommates,
    })
