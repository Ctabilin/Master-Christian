# Generated by Django 5.1.1 on 2024-12-02 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ArnoldTONY', '0007_product_user_description_product_user_design_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
