"""Show a student's attendance history inside any page, for example the student profile.

    {% load attendance_tags %}
    {% attendance_history student %}
"""
from django import template

from attendance import services

register = template.Library()


@register.inclusion_tag('attendance/_history_table.html')
def attendance_history(student, limit=30):
    records = list(services.student_history(student)[:limit]) if student is not None else []
    for record in records:
        record.duration = services.format_duration(record.check_in_at, record.check_out_at)
    return {'records': records, 'limit': limit}
