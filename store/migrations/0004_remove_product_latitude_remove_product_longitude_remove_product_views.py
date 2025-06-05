from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_product_listing_type_alter_product_condition'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='product',
            name='longitude',
        ),
        migrations.RemoveField(
            model_name='product',
            name='views',
        ),
    ] 