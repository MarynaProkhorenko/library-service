# Generated by Django 4.2 on 2023-04-19 06:51

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("book_service", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="inventory",
            field=models.IntegerField(
                default=0, validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
    ]
