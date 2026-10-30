"""Add reviewer_remarks column to LeaveApplication (FR-09)."""
from django.db import migrations


def add_reviewer_remarks(apps, schema_editor):
    from core.models import LeaveApplication

    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = {c.name for c in connection.introspection.get_table_description(cursor, LeaveApplication._meta.db_table)}

    if 'reviewer_remarks' not in columns:
        quote = schema_editor.quote_name
        sql = f"ALTER TABLE {quote(LeaveApplication._meta.db_table)} ADD COLUMN {quote('reviewer_remarks')} text NOT NULL DEFAULT ''"
        schema_editor.execute(sql)


class Migration(migrations.Migration):
    dependencies = [('core', '0005_visitor_id_proof')]
    operations = [migrations.RunPython(add_reviewer_remarks, migrations.RunPython.noop)]
