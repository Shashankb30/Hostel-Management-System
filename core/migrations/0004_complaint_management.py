"""Complaint management (FR-06): new complaint columns, DemeritRule and ComplaintUpdate tables.

Same approach as 0002 and 0003: 0001 builds tables from the live model registry, so a
brand-new database already has everything below. This migration only adds what is missing,
which is the case for databases that applied 0001 before FR-06 existed. It then converts any
old severity/status values and makes sure the default demerit rules are present.

The columns are added with plain ``ALTER TABLE ... ADD COLUMN``. Django's own ``add_field`` is
not safe here on SQLite: it rebuilds the table from the live model, which already has every
new column, so columns that are still missing get filled with their own names.
"""
from django.db import migrations, models

DEFAULT_RULES = [
    ('minor', 1, 'Minor breach of hostel rules'),
    ('moderate', 3, 'Repeated or disruptive breach of hostel rules'),
    ('major', 5, 'Serious misconduct'),
]

NEW_COMPLAINT_FIELDS = ['kind', 'category', 'remarks', 'raised_by', 'is_escalated', 'escalation_reason']

# Values used before FR-06 -> the values used now.
OLD_SEVERITIES = {'low': 'minor', 'medium': 'moderate', 'high': 'major', 'critical': 'major'}
OLD_STATUSES = {'investigating': 'under_review', 'rejected': 'resolved'}


def _add_column(schema_editor, model, field):
    """ALTER TABLE ... ADD COLUMN for one field, plus its index."""
    connection = schema_editor.connection
    quote = schema_editor.quote_name
    sql = f'ALTER TABLE {quote(model._meta.db_table)} ADD COLUMN {quote(field.column)} {field.db_type(connection)}'
    if field.remote_field is not None:
        target = field.remote_field.model._meta
        sql += (f' NULL REFERENCES {quote(target.db_table)} ({quote(target.pk.column)})'
                ' DEFERRABLE INITIALLY DEFERRED')
    else:
        sql += f' NOT NULL DEFAULT {schema_editor.quote_value(field.get_default())}'
    schema_editor.execute(sql)
    if field.db_index or field.remote_field is not None:
        schema_editor.add_index(model, models.Index(fields=[field.name], name=f'ix_complaint_{field.name}'))


def apply_complaint_management(apps, schema_editor):
    from core.models import Complaint, ComplaintUpdate, DemeritRule

    connection = schema_editor.connection
    tables = connection.introspection.table_names()
    for model in (DemeritRule, ComplaintUpdate):
        if model._meta.db_table not in tables:
            schema_editor.create_model(model)

    with connection.cursor() as cursor:
        columns = {c.name for c in connection.introspection.get_table_description(cursor, Complaint._meta.db_table)}
    for name in NEW_COMPLAINT_FIELDS:
        field = Complaint._meta.get_field(name)
        if field.column not in columns:
            _add_column(schema_editor, Complaint, field)

    for old, new in OLD_SEVERITIES.items():
        Complaint.objects.filter(severity=old).update(severity=new)
    for old, new in OLD_STATUSES.items():
        Complaint.objects.filter(status=old).update(status=new)

    # Added last: on SQLite this rebuilds the table, so every column must exist by now.
    with connection.cursor() as cursor:
        existing = connection.introspection.get_constraints(cursor, Complaint._meta.db_table)
    for constraint in Complaint._meta.constraints:
        if constraint.name not in existing and not Complaint.objects.filter(description='').exists():
            schema_editor.add_constraint(Complaint, constraint)

    for severity, points, description in DEFAULT_RULES:
        DemeritRule.objects.get_or_create(
            severity=severity, defaults={'points': points, 'description': description})


class Migration(migrations.Migration):
    dependencies = [('core', '0003_allocationrule')]
    operations = [migrations.RunPython(apply_complaint_management, migrations.RunPython.noop)]
