"""Add id_proof column to VisitorLog (FR-08)."""
from django.db import migrations, models


def add_id_proof(apps, schema_editor):
    from core.models import VisitorLog

    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = {c.name for c in connection.introspection.get_table_description(cursor, VisitorLog._meta.db_table)}

    if 'id_proof' not in columns:
        quote = schema_editor.quote_name
        sql = f"ALTER TABLE {quote(VisitorLog._meta.db_table)} ADD COLUMN {quote('id_proof')} varchar(50) NOT NULL DEFAULT ''"
        schema_editor.execute(sql)


class Migration(migrations.Migration):
    dependencies = [('core', '0004_complaint_management')]
    operations = [migrations.RunPython(add_id_proof, migrations.RunPython.noop)]
