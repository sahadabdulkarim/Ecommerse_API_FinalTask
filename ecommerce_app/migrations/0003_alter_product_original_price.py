# Generated by Django 4.2.3 on 2023-08-12 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0002_product_original_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='original_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
