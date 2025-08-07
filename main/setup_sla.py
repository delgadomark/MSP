#!/usr/bin/env python
import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

# Import after Django setup
from helpdesk.models import Priority, SLALevel  # pylint: disable=wrong-import-position

# Create SLA levels
sla_data = [
    (Priority.LOW, 48, 168),  # 48h response, 1 week resolution
    (Priority.MEDIUM, 24, 72),  # 24h response, 3 days resolution
    (Priority.HIGH, 8, 24),  # 8h response, 1 day resolution
    (Priority.URGENT, 2, 8),  # 2h response, 8h resolution
]

for priority, response_hours, resolution_hours in sla_data:
    sla, created = SLALevel.objects.get_or_create(
        priority=priority,
        defaults={
            "response_time_hours": response_hours,
            "resolution_time_hours": resolution_hours,
        },
    )
    if created:
        print(
            f"Created SLA level for {priority}: {response_hours}h response, {resolution_hours}h"
            " resolution"
        )
    else:
        print(f"SLA level for {priority} already exists")

print("SLA setup complete!")
