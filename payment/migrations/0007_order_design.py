# Generated by Django 5.1.1 on 2024-12-01 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0006_customersubmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='design',
            field=models.ImageField(blank=True, null=True, upload_to='customer_design/'),
        ),
    ]
