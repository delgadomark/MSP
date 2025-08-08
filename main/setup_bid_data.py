#!/usr/bin/env python
"""
Setup sample data for the bid sheets system
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import django

# Setup Django environment
sys.path.append("/workspaces/simple-django/main")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BLT.settings")
django.setup()

from bidsheets.models import (
    BidItem,
    BidSheet,
    CompanyInfo,
    Customer,
    ServiceCategory,
    ServiceItem,
)
from django.contrib.auth import get_user_model

User = get_user_model()


def create_sample_data():
    print("Creating sample bid sheet data...")

    # Create or get company info
    company_info, created = CompanyInfo.objects.get_or_create(
        defaults={
            "name": "Blue Line Technology",
            "address": "814 E. 10th Street\nAlamogordo, NM 88310",
            "phone": "575-479-7470",
            "email": "info@bluetech.com",
            "website": "https://www.bluetech.com",
            "default_terms": (
                "Payment is due within 30 days of invoice date. "
                "50% deposit required before work begins. "
                "Final payment due upon completion. "
                "Late payments subject to 1.5% monthly service charge."
            ),
            "default_exclusions": (
                "Permits and licensing fees\n"
                "Electrical work requiring licensed electrician\n"
                "Structural modifications\n"
                "Unforeseen complications or changes to scope\n"
                "Travel time beyond 50 miles from our location"
            ),
        }
    )
    print(f"Company info {'created' if created else 'updated'}")

    # Create service categories
    categories_data = [
        ("Computer Repair", "Hardware and software computer repair services", 1),
        ("Network Setup", "Network installation and configuration", 2),
        ("Software Installation", "Software setup and configuration", 3),
        ("Consultation", "Technical consultation and planning", 4),
        ("Training", "User training and education", 5),
        ("Maintenance", "Ongoing maintenance and support", 6),
    ]

    categories = {}
    for name, desc, order in categories_data:
        category, created = ServiceCategory.objects.get_or_create(
            name=name, defaults={"description": desc, "sort_order": order}
        )
        categories[name] = category
        print(f"Category '{name}' {'created' if created else 'exists'}")

    # Create service items
    services_data = [
        # Computer Repair
        (
            "Computer Repair",
            "Virus Removal",
            "Complete virus and malware removal",
            75.00,
            "each",
        ),
        (
            "Computer Repair",
            "Hardware Diagnostic",
            "Comprehensive hardware testing and diagnosis",
            50.00,
            "each",
        ),
        (
            "Computer Repair",
            "Memory Upgrade",
            "RAM installation and upgrade",
            25.00,
            "each",
        ),
        (
            "Computer Repair",
            "Hard Drive Replacement",
            "HDD/SSD replacement and data transfer",
            100.00,
            "each",
        ),
        (
            "Computer Repair",
            "Operating System Installation",
            "Fresh OS installation and setup",
            150.00,
            "each",
        ),
        # Network Setup
        (
            "Network Setup",
            "Router Installation",
            "Router setup and configuration",
            125.00,
            "each",
        ),
        (
            "Network Setup",
            "WiFi Network Setup",
            "Wireless network configuration",
            100.00,
            "each",
        ),
        (
            "Network Setup",
            "Network Cable Installation",
            "Ethernet cable installation",
            15.00,
            "linear ft",
        ),
        (
            "Network Setup",
            "Network Security Setup",
            "Firewall and security configuration",
            200.00,
            "each",
        ),
        (
            "Network Setup",
            "Network Printer Setup",
            "Network printer installation and sharing",
            75.00,
            "each",
        ),
        # Software Installation
        (
            "Software Installation",
            "Office Suite Installation",
            "Microsoft Office or similar installation",
            75.00,
            "each",
        ),
        (
            "Software Installation",
            "Antivirus Setup",
            "Antivirus software installation and configuration",
            50.00,
            "each",
        ),
        (
            "Software Installation",
            "Backup Software Setup",
            "Automated backup solution setup",
            100.00,
            "each",
        ),
        (
            "Software Installation",
            "Custom Software Installation",
            "Specialized software installation",
            60.00,
            "each",
        ),
        # Consultation
        (
            "Consultation",
            "Technical Consultation",
            "On-site technical consultation",
            85.00,
            "hour",
        ),
        (
            "Consultation",
            "System Planning",
            "IT system design and planning",
            100.00,
            "hour",
        ),
        (
            "Consultation",
            "Security Assessment",
            "Network and system security evaluation",
            125.00,
            "hour",
        ),
        # Training
        (
            "Training",
            "Basic Computer Training",
            "Basic computer skills training",
            60.00,
            "hour",
        ),
        (
            "Training",
            "Software Training",
            "Application-specific training",
            70.00,
            "hour",
        ),
        (
            "Training",
            "Network Administration Training",
            "Advanced network management training",
            100.00,
            "hour",
        ),
        # Maintenance
        (
            "Maintenance",
            "System Maintenance",
            "Regular system maintenance and updates",
            75.00,
            "hour",
        ),
        (
            "Maintenance",
            "Remote Support",
            "Remote technical support session",
            50.00,
            "hour",
        ),
        (
            "Maintenance",
            "Preventive Maintenance",
            "Preventive system maintenance",
            85.00,
            "hour",
        ),
    ]

    for cat_name, service_name, desc, price, unit in services_data:
        service, created = ServiceItem.objects.get_or_create(
            category=categories[cat_name],
            name=service_name,
            defaults={
                "description": desc,
                "default_unit_price": Decimal(str(price)),
                "unit_type": unit,
                "is_active": True,
            },
        )
        if created:
            print(f"Service '{service_name}' created")

    # Create sample customers
    customers_data = [
        (
            "John Smith",
            "Smith Consulting",
            "john@smithconsulting.com",
            "575-555-0101",
            "123 Main St\nAlamogordo, NM 88310",
        ),
        (
            "Sarah Johnson",
            "Johnson Law Firm",
            "sarah@johnsonlaw.com",
            "575-555-0102",
            "456 Oak Ave\nAlamogordo, NM 88310",
        ),
        (
            "Mike Davis",
            "",
            "mike.davis@email.com",
            "575-555-0103",
            "789 Pine St\nAlamogordo, NM 88310",
        ),
        (
            "Lisa Rodriguez",
            "Rodriguez Accounting",
            "lisa@rodriguezacc.com",
            "575-555-0104",
            "321 Elm St\nAlamogordo, NM 88310",
        ),
        (
            "Tom Wilson",
            "Wilson Real Estate",
            "tom@wilsonrealty.com",
            "575-555-0105",
            "654 Cedar Ave\nAlamogordo, NM 88310",
        ),
    ]

    customers = {}
    for name, company, email, phone, address in customers_data:
        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "company": company,
                "phone": phone,
                "address": address,
            },
        )
        customers[name] = customer
        print(f"Customer '{name}' {'created' if created else 'exists'}")

    # Create a superuser if it doesn't exist
    if not User.objects.filter(is_superuser=True).exists():
        admin_user = User.objects.create_superuser(
            username="admin", email="admin@bluetech.com", password="admin123"
        )
        print("Admin user created (username: admin, password: admin123)")
    else:
        admin_user = User.objects.filter(is_superuser=True).first()
        print("Using existing admin user")

    # Create sample bid sheets
    bid_data = [
        (
            "Office Network Upgrade",
            "John Smith",
            "Complete network infrastructure upgrade for office",
            "123 Main St Office",
            [
                ("Router Installation", 1, 125.00),
                ("Network Cable Installation", 150, 15.00),
                ("Network Security Setup", 1, 200.00),
                ("Network Printer Setup", 2, 75.00),
                ("Technical Consultation", 4, 85.00),
            ],
            10.0,
            8.5,
        ),
        (
            "Computer Repair Package",
            "Sarah Johnson",
            "Multiple computer repairs and upgrades",
            "Johnson Law Firm",
            [
                ("Virus Removal", 3, 75.00),
                ("Memory Upgrade", 2, 25.00),
                ("Hard Drive Replacement", 1, 100.00),
                ("Operating System Installation", 1, 150.00),
                ("Antivirus Setup", 3, 50.00),
            ],
            5.0,
            8.5,
        ),
        (
            "Home Office Setup",
            "Mike Davis",
            "Complete home office technology setup",
            "789 Pine St",
            [
                ("Computer Repair", 1, 75.00),
                ("WiFi Network Setup", 1, 100.00),
                ("Office Suite Installation", 1, 75.00),
                ("Backup Software Setup", 1, 100.00),
                ("Basic Computer Training", 2, 60.00),
            ],
            0.0,
            8.5,
        ),
    ]

    for title, customer_name, description, address, items, discount, tax in bid_data:
        customer = customers[customer_name]

        bid, created = BidSheet.objects.get_or_create(
            title=title,
            customer=customer,
            defaults={
                "project_description": description,
                "project_address": address,
                "valid_until": date.today() + timedelta(days=30),
                "discount_percentage": Decimal(str(discount)),
                "tax_percentage": Decimal(str(tax)),
                "created_by": admin_user,
                "status": "draft",
            },
        )

        if created:
            print(f"Bid '{title}' created")

            # Add bid items
            for item_name, qty, price in items:
                try:
                    service_item = ServiceItem.objects.get(name=item_name)
                except ServiceItem.DoesNotExist:
                    service_item = None

                BidItem.objects.create(
                    bid=bid,
                    service_item=service_item,
                    description=item_name,
                    quantity=Decimal(str(qty)),
                    unit_price=Decimal(str(price)),
                    unit_type=(
                        "each"
                        if qty == 1
                        else (
                            "hour"
                            if "Training" in item_name or "Consultation" in item_name
                            else "linear ft" if "Cable" in item_name else "each"
                        )
                    ),
                )

            # Recalculate totals
            bid.recalculate_totals()
            print(f"  Added {len(items)} items to bid")

    print("\nSample data creation completed!")
    print("\nYou can now:")
    print("1. Access the admin panel at /admin/ (username: admin, password: admin123)")
    print("2. View bid sheets at /bids/")
    print("3. Create new customers and service items")
    print("4. Generate PDF reports")
    print("5. Send emails (requires email configuration)")


if __name__ == "__main__":
    create_sample_data()
    print("4. Generate PDF reports")
    print("5. Send emails (requires email configuration)")

if __name__ == "__main__":
    create_sample_data()
