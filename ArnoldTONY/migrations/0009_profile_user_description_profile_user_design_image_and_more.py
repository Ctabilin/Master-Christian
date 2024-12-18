# Generated by Django 5.1.1 on 2024-12-03 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ArnoldTONY', '0008_product_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='user_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='user_design_image',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/user_design/'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='date_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
