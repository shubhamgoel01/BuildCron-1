# Generated by Django 3.2.4 on 2021-07-20 00:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BuildCron', '0002_auto_20210707_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licenses',
            name='start_date',
            field=models.DateField(),
        ),
    ]
