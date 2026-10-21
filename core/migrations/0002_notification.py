"""Add the notification table (Issue #14, SETUP.13).

0001 builds tables from the live model registry, so on a brand-new database it already
creates this table too. This migration therefore only creates it when it is missing,
which is the case for databases that applied 0001 before Notification existed.
The reverse step does nothing: reversing 0001 drops every core table, Notification included.
"""
from django.db import migrations


def create_notification_table(apps, schema_editor):
    from core.models import Notification
    if Notification._meta.db_table not in schema_editor.connection.introspection.table_names():
        schema_editor.create_model(Notification)


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]
    operations = [migrations.RunPython(create_notification_table, migrations.RunPython.noop)]
