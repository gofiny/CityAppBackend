# Generated by Django 3.0.2 on 2020-01-10 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_delete_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='dynamicobject',
            name='power',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='dynamicobject',
            name='speed',
            field=models.IntegerField(default=10),
        ),
    ]
