from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_stockhistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='stock',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='low_stock_threshold',
            field=models.DecimalField(decimal_places=2, default=5, max_digits=10),
        ),
        migrations.AlterField(
            model_name='stockhistory',
            name='quantity',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
