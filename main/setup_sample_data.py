#!/usr/bin/env python
import os

import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

# Import after Django setup
from helpdesk.models import (  # pylint: disable=wrong-import-position
    Category,
    CustomerInfo,
    Priority,
    SLALevel,
    Status,
    Ticket,
)

User = get_user_model()


def create_admin_user():
    """Create admin user if it doesn't exist"""
    if not User.objects.filter(username="admin").exists():
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@bluelinetech.org",
            password="admin123",
            first_name="Admin",
            last_name="User",
        )
        print(f"Created admin user: {admin.username}")
    else:
        print("Admin user already exists")


def create_sla_levels():
    """Create SLA levels"""
    sla_data = [
        (Priority.LOW, 48, 168),  # 48h response, 1 week resolution
        (Priority.MEDIUM, 24, 72),  # 24h response, 3 days resolution
        (Priority.HIGH, 8, 24),  # 8h response, 1 day resolution
        (Priority.URGENT, 2, 8),  # 2h response, 8h resolution
    ]

    for priority, response_hours, resolution_hours in sla_data:
        _, created = SLALevel.objects.get_or_create(
            priority=priority,
            defaults={
                "response_time_hours": response_hours,
                "resolution_time_hours": resolution_hours,
            },
        )
        if created:
            print(
                f"Created SLA level for {priority}: {response_hours}h response,"
                f" {resolution_hours}h resolution"
            )


def create_sample_customers():
    """Create sample customer information"""
    customers_data = [
        {
            "customer_name": "John Smith",
            "customer_email": "john.smith@company.com",
            "company": "Tech Solutions Inc",
            "phone": "(555) 123-4567",
            "computer_make": "Dell",
            "computer_model": "Latitude 7420",
            "operating_system": "Windows 11",
            "os_version": "22H2",
            "serial_number": "DL7420001",
            "notes": "Primary workstation, requires specialized CAD software",
        },
        {
            "customer_name": "Sarah Johnson",
            "customer_email": "sarah.j@startup.io",
            "company": "Startup Innovations",
            "phone": "(555) 987-6543",
            "computer_make": "Apple",
            "computer_model": 'MacBook Pro 16"',
            "operating_system": "macOS Monterey",
            "os_version": "12.6",
            "serial_number": "MBP16002",
            "notes": "Development machine, has Docker and multiple VMs running",
        },
    ]

    for customer_data in customers_data:
        customer, created = CustomerInfo.objects.get_or_create(
            customer_email=customer_data["customer_email"], defaults=customer_data
        )
        if created:
            print(f"Created customer: {customer.customer_name}")


def create_sample_tickets():
    """Create sample tickets"""
    admin_user = User.objects.filter(is_staff=True).first()

    tickets_data = [
        {
            "title": "Email not syncing on mobile device",
            "description": (
                "User reports that emails are not syncing properly on their iPhone. Last sync was"
                " 2 days ago."
            ),
            "customer_name": "John Smith",
            "customer_email": "john.smith@company.com",
            "customer_phone": "(555) 123-4567",
            "category": Category.TECHNICAL,
            "priority": Priority.MEDIUM,
            "status": Status.NEW,
        },
        {
            "title": "Computer running very slowly",
            "description": (
                "MacBook Pro is taking 5+ minutes to boot up and applications are very slow to"
                " load."
            ),
            "customer_name": "Sarah Johnson",
            "customer_email": "sarah.j@startup.io",
            "customer_phone": "(555) 987-6543",
            "category": Category.HARDWARE,
            "priority": Priority.HIGH,
            "status": Status.ASSIGNED,
            "assigned_to": admin_user,
        },
        {
            "title": "Unable to access shared network drive",
            "description": (
                'Getting "access denied" error when trying to connect to \\\\server\\shared-docs'
                " folder."
            ),
            "customer_name": "Mike Wilson",
            "customer_email": "mike.w@consulting.biz",
            "customer_phone": "(555) 456-7890",
            "category": Category.NETWORK,
            "priority": Priority.URGENT,
            "status": Status.IN_PROGRESS,
            "assigned_to": admin_user,
        },
    ]

    for ticket_data in tickets_data:
        if not Ticket.objects.filter(
            customer_email=ticket_data["customer_email"], title=ticket_data["title"]
        ).exists():
            ticket = Ticket.objects.create(**ticket_data)
            print(f"Created ticket: {ticket.ticket_number} - {ticket.title}")


if __name__ == "__main__":
    print("Setting up helpdesk sample data...")
    create_admin_user()
    create_sla_levels()
    create_sample_customers()
    create_sample_tickets()
    print("Sample data setup complete!")
    print("\nYou can now:")
    print("- Login to admin at /admin/ with username: admin, password: admin123")
    print("- Visit the ticket dashboard at /tickets/")
    print("- Create new tickets at /tickets/create/")
