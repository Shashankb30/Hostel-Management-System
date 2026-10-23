"""Add the allocation priority rule table (Issue #55, FR-04.03).

Same approach as 0002: 0001 builds tables from the live model registry, so a brand-new
database already has this table. It is only created here when missing, which is the case
for databases that applied 0001 before AllocationRule existed.
"""
from django.db import migrations


def create_allocation_rule_table(apps, schema_editor):
    from core.models import AllocationRule
    if AllocationRule._meta.db_table not in schema_editor.connection.introspection.table_names():
        schema_editor.create_model(AllocationRule)


class Migration(migrations.Migration):
    dependencies = [('core', '0002_notification')]
    operations = [migrations.RunPython(create_allocation_rule_table, migrations.RunPython.noop)]
