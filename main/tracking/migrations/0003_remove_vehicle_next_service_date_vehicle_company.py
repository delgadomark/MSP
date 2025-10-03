# Generated manually to replace next_service_date with company field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0002_vehicle_current_driver_vehicle_current_mileage_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="vehicle",
            name="next_service_date",
        ),
        migrations.AddField(
            model_name="vehicle",
            name="company",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
