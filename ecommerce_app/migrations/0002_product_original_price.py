# Generated by Django 4.2.3 on 2023-08-12 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='original_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]
