from django.contrib import admin
from .models import (Hostel, UserAccount, Student, Room, Allocation, AllocationRequest,
                     FeeRecord, Payment, Complaint, DemeritRecord, AttendanceRecord,
                     VisitorLog, LeaveApplication, Notice, Notification)

for model in (Hostel, UserAccount, Student, Room, Allocation, AllocationRequest,
              FeeRecord, Payment, Complaint, DemeritRecord, AttendanceRecord,
              VisitorLog, LeaveApplication, Notice, Notification):
    admin.site.register(model)
