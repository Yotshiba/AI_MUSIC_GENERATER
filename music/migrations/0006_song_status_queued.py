"""
Add 'Queued' choice to Song.status (REQ-4.3.4 / UC-01 E4).
This is a choices-only change — no schema alteration needed.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0005_generationlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='status',
            field=models.CharField(
                choices=[
                    ('Draft', 'Draft'),
                    ('Queued', 'Queued'),
                    ('Generating', 'Generating'),
                    ('Completed', 'Completed'),
                    ('Failed', 'Failed'),
                ],
                default='Draft',
                max_length=12,
            ),
        ),
    ]
