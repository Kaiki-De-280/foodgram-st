# Generated by Django 3.2.16 on 2025-05-17 11:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20250515_2058'),
    ]

    operations = [
        # migrations.RemoveField(
        #     model_name='shoppingcart',
        #     name='recipe',
        # ),
        # migrations.RemoveField(
        #     model_name='shoppingcart',
        #     name='user',
        # ),
        migrations.DeleteModel(
            name='Favorite',
        ),
        migrations.DeleteModel(
            name='ShoppingCart',
        ),
    ]
