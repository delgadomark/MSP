import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from printdesign.models import (
    PrintCustomer,
    PrintEstimate,
    PrintEstimateItem,
    PrintServiceCategory,
    PrintServiceItem,
    ProductSheet,
)
from tracking.models import InstallationSchedule, ProjectCard, Vehicle, VehicleDropOff


class Command(BaseCommand):
    help = "Create sample data for Blue Line Print & Design system"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5, help="Number of users to create")
        parser.add_argument(
            "--customers",
            type=int,
            default=20,
            help="Number of print customers to create",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Creating sample data...")

            # Create users with profiles
            self.create_users(options["users"])

            # Create print service categories
            self.create_service_categories()

            # Create print service items
            self.create_service_items()

            # Create product sheets
            self.create_product_sheets()

            # Create print customers
            self.create_print_customers(options["customers"])

            # Create print estimates
            self.create_print_estimates()

            # Create vehicles
            self.create_vehicles()

            # Create project cards
            self.create_project_cards()

            # Create installations and drop-offs
            self.create_installations()

            self.stdout.write(self.style.SUCCESS("Successfully created sample data!"))

    def create_users(self, count):
        """Create sample users with different access levels"""
        self.stdout.write("Creating users...")

        # Create admin user if not exists
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@bluelinetech.org",
                password="admin123",
                first_name="System",
                last_name="Administrator",
            )
        else:
            admin = User.objects.get(username="admin")

        # Create or get admin profile
        UserProfile.objects.get_or_create(
            user=admin,
            defaults={"can_access_technology": True, "can_access_print_design": True},
        )

        # Create master user
        if not User.objects.filter(username="master").exists():
            master = User.objects.create_user(
                username="master",
                email="master@bluelinetech.org",
                password="master123",
                first_name="Master",
                last_name="User",
            )
        else:
            master = User.objects.get(username="master")

        UserProfile.objects.get_or_create(
            user=master,
            defaults={"can_access_technology": True, "can_access_print_design": True},
        )

        # Create tech users
        for i in range(2):
            username = f"tech{i+1}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@bluelinetech.org",
                    password="tech123",
                    first_name=f"Tech",
                    last_name=f"User {i+1}",
                )
            else:
                user = User.objects.get(username=username)

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "can_access_technology": True,
                    "can_access_print_design": False,
                },
            )

        # Create print users
        for i in range(2):
            username = f"print{i+1}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@bluelinetech.org",
                    password="print123",
                    first_name=f"Print",
                    last_name=f"Designer {i+1}",
                )
            else:
                user = User.objects.get(username=username)

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "can_access_technology": False,
                    "can_access_print_design": True,
                },
            )

    def create_service_categories(self):
        """Create print service categories"""
        self.stdout.write("Creating service categories...")

        categories = [
            ("Business Cards", "Professional business card printing"),
            ("Banners & Signs", "Large format printing and signage"),
            ("Marketing Materials", "Brochures, flyers, and promotional items"),
            ("Stationery", "Letterheads, envelopes, and office supplies"),
            ("Vehicle Graphics", "Car wraps and vehicle decals"),
            ("Promotional Products", "Branded merchandise and gifts"),
        ]

        for name, description in categories:
            PrintServiceCategory.objects.get_or_create(
                name=name, defaults={"description": description, "is_active": True}
            )

    def create_service_items(self):
        """Create print service items"""
        self.stdout.write("Creating service items...")

        categories = PrintServiceCategory.objects.all()

        service_items = [
            # Business Cards
            (
                "Standard Business Cards",
                categories.get(name="Business Cards"),
                "each",
                0.25,
                "standard",
                "none",
                250,
                5000,
            ),
            (
                "Premium Business Cards",
                categories.get(name="Business Cards"),
                "each",
                0.45,
                "premium",
                "uv_coating",
                100,
                2500,
            ),
            (
                "Plastic Business Cards",
                categories.get(name="Business Cards"),
                "each",
                1.25,
                "plastic",
                "none",
                50,
                1000,
            ),
            # Banners & Signs
            (
                "Vinyl Banner",
                categories.get(name="Banners & Signs"),
                "sqft",
                3.50,
                "vinyl",
                "none",
                10,
                1000,
            ),
            (
                "Yard Signs",
                categories.get(name="Banners & Signs"),
                "each",
                12.00,
                "coroplast",
                "none",
                1,
                100,
            ),
            (
                "A-Frame Signs",
                categories.get(name="Banners & Signs"),
                "each",
                85.00,
                "aluminum",
                "weather_resistant",
                1,
                50,
            ),
            # Marketing Materials
            (
                "Tri-Fold Brochures",
                categories.get(name="Marketing Materials"),
                "each",
                0.75,
                "glossy",
                "none",
                100,
                10000,
            ),
            (
                "Flyers 8.5x11",
                categories.get(name="Marketing Materials"),
                "each",
                0.15,
                "standard",
                "none",
                250,
                25000,
            ),
            (
                "Postcards",
                categories.get(name="Marketing Materials"),
                "each",
                0.35,
                "cardstock",
                "uv_coating",
                100,
                10000,
            ),
            # Vehicle Graphics
            (
                "Car Door Decals",
                categories.get(name="Vehicle Graphics"),
                "each",
                45.00,
                "vinyl",
                "laminated",
                2,
                100,
            ),
            (
                "Full Vehicle Wrap",
                categories.get(name="Vehicle Graphics"),
                "each",
                2500.00,
                "vinyl",
                "laminated",
                1,
                10,
            ),
            (
                "Window Graphics",
                categories.get(name="Vehicle Graphics"),
                "sqft",
                8.50,
                "perforated_vinyl",
                "none",
                5,
                500,
            ),
        ]

        for (
            name,
            category,
            unit_type,
            base_price,
            paper_type,
            finish_type,
            min_qty,
            max_qty,
        ) in service_items:
            PrintServiceItem.objects.get_or_create(
                name=name,
                category=category,
                defaults={
                    "unit_type": unit_type,
                    "base_price": Decimal(str(base_price)),
                    "paper_type": paper_type,
                    "finish_type": finish_type,
                    "min_quantity": min_qty,
                    "max_quantity": max_qty,
                    "tier_1_qty": min_qty * 2,
                    "tier_1_price": Decimal(str(base_price * 0.9)),
                    "tier_2_qty": min_qty * 5,
                    "tier_2_price": Decimal(str(base_price * 0.8)),
                    "tier_3_qty": min_qty * 10,
                    "tier_3_price": Decimal(str(base_price * 0.7)),
                    "production_time_days": random.randint(1, 7),
                    "is_active": True,
                },
            )

    def create_product_sheets(self):
        """Create product sheets"""
        self.stdout.write("Creating product sheets...")

        products = [
            (
                "Business Card Package",
                "business_cards",
                "Complete business card design and printing package",
                299.00,
            ),
            (
                "Starter Marketing Kit",
                "marketing_package",
                "Business cards, letterhead, and brochure design",
                599.00,
            ),
            (
                "Vehicle Wrap Design",
                "vehicle_graphics",
                "Complete vehicle wrap design and installation",
                2999.00,
            ),
            (
                "Event Banner Package",
                "banners",
                "Multiple banner sizes for events and trade shows",
                450.00,
            ),
            (
                "Logo Design Service",
                "design_service",
                "Professional logo design with 3 concepts",
                350.00,
            ),
        ]

        for name, product_type, description, base_price in products:
            ProductSheet.objects.get_or_create(
                name=name,
                defaults={
                    "product_type": product_type,
                    "description": description,
                    "base_price": Decimal(str(base_price)),
                    "min_quantity": 1,
                    "production_time_days": random.randint(3, 14),
                    "setup_required": True,
                    "design_included": True,
                    "is_active": True,
                    "featured": random.choice([True, False]),
                    "sort_order": random.randint(1, 100),
                },
            )

    def create_print_customers(self, count):
        """Create print customers"""
        self.stdout.write(f"Creating {count} print customers...")

        companies = [
            "ABC Marketing",
            "XYZ Corp",
            "Local Restaurant",
            "Tech Startup Inc",
            "Medical Practice",
            "Law Firm LLC",
            "Real Estate Agency",
            "Auto Repair Shop",
            "Consulting Group",
            "Retail Store",
            "Construction Company",
            "Non-Profit Org",
            "Photography Studio",
            "Dental Office",
            "Insurance Agency",
            "Hair Salon",
            "Coffee Shop",
            "Fitness Center",
            "Pet Store",
            "Flower Shop",
        ]

        states = ["NM", "TX", "AZ", "CO", "UT", "NV", "CA", "OK"]
        cities = [
            "Albuquerque",
            "Santa Fe",
            "Las Cruces",
            "Roswell",
            "Farmington",
            "Clovis",
        ]

        for i in range(count):
            if PrintCustomer.objects.filter(email=f"customer{i+1}@example.com").exists():
                continue

            PrintCustomer.objects.create(
                name=f"Customer {i+1}",
                company=(random.choice(companies) if random.choice([True, False]) else ""),
                customer_type=random.choice(
                    ["individual", "business", "non_profit", "government"]
                ),
                email=f"customer{i+1}@example.com",
                phone=f"(575) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
                address=f"{random.randint(100, 9999)} Main St",
                city=random.choice(cities),
                state=random.choice(states),
                zip_code=f"{random.randint(87000, 89000)}",
                preferred_contact_method=random.choice(["email", "phone", "text"]),
                tax_exempt=(random.choice([True, False]) if random.random() < 0.2 else False),
                credit_approved=(random.choice([True, False]) if random.random() < 0.3 else False),
                credit_limit=(
                    Decimal(str(random.randint(500, 5000)))
                    if random.random() < 0.3
                    else Decimal("0")
                ),
            )

    def create_print_estimates(self):
        """Create print estimates"""
        self.stdout.write("Creating print estimates...")

        customers = list(PrintCustomer.objects.all())
        service_items = list(PrintServiceItem.objects.all())
        users = list(User.objects.filter(profile__can_access_print_design=True))

        for i in range(15):
            customer = random.choice(customers)
            created_by = random.choice(users)

            estimate = PrintEstimate.objects.create(
                customer=customer,
                title=f"Print Project {i+1}",
                description=f"Print project for {customer.name}",
                status=random.choice(["draft", "sent", "approved", "declined", "completed"]),
                created_date=date.today() - timedelta(days=random.randint(0, 30)),
                valid_until=date.today() + timedelta(days=30),
                tax_percentage=Decimal("8.25"),
                created_by=created_by,
            )

            # Add estimate items
            num_items = random.randint(1, 4)
            for j in range(num_items):
                service_item = random.choice(service_items)
                quantity = random.randint(
                    service_item.min_quantity, min(service_item.max_quantity, 1000)
                )

                PrintEstimateItem.objects.create(
                    estimate=estimate,
                    service_item=service_item,
                    description=f"{service_item.name} - Custom Design",
                    quantity=Decimal(str(quantity)),
                    unit_price=service_item.base_price,
                    total_price=service_item.base_price * quantity,
                    setup_fee=(
                        Decimal("25.00") if random.choice([True, False]) else Decimal("0.00")
                    ),
                    requires_design=random.choice([True, False]),
                )

            # Update estimate totals
            estimate.recalculate_totals()
            estimate.save()

    def create_vehicles(self):
        """Create sample vehicles"""
        self.stdout.write("Creating vehicles...")

        makes = ["Ford", "Chevrolet", "Toyota", "Honda", "Nissan", "RAM", "GMC"]
        models = ["F-150", "Silverado", "Camry", "Civic", "Altima", "1500", "Sierra"]
        colors = ["White", "Black", "Silver", "Blue", "Red", "Gray"]

        customers = list(PrintCustomer.objects.all()[:10])  # Use first 10 customers

        for i in range(8):
            make = random.choice(makes)
            model = random.choice(models)
            year = random.randint(2015, 2024)

            Vehicle.objects.create(
                license_plate=(
                    f"NM-{random.randint(100, 999)}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}"
                ),
                make=make,
                model=model,
                year=year,
                color=random.choice(colors),
                vin=f"1{random.randint(10000000000000000, 99999999999999999)}",
                print_customer=(
                    random.choice(customers) if random.choice([True, False]) else None
                ),
                notes=f"Customer vehicle for {make} {model}",
            )

    def create_project_cards(self):
        """Create project tracking cards"""
        self.stdout.write("Creating project cards...")

        customers = list(PrintCustomer.objects.all())
        users = list(User.objects.all())
        estimates = list(PrintEstimate.objects.all())

        tech_statuses = [
            "tech_backlog",
            "tech_in_progress",
            "tech_awaiting_client",
            "tech_testing",
            "tech_completed",
        ]
        print_statuses = [
            "print_design_brief",
            "print_design_phase",
            "print_client_approval",
            "print_production",
            "print_quality_check",
            "print_delivered",
        ]

        # Create technology project cards
        for i in range(8):
            ProjectCard.objects.create(
                title=f"Tech Project {i+1}",
                description=f"Technology project for customer support and maintenance",
                department="technology",
                status=random.choice(tech_statuses),
                priority=random.choice(["low", "medium", "high", "urgent"]),
                assigned_to=random.choice(users),
                sla_hours=random.choice([4, 8, 24, 48]),
                sla_due_date=timezone.now() + timedelta(hours=random.choice([4, 8, 24, 48])),
                sla_breached=(random.choice([True, False]) if random.random() < 0.2 else False),
                sort_order=i,
                created_by=random.choice(users),
            )

        # Create print project cards
        available_estimates = list(estimates)  # Copy the list
        for i in range(10):
            customer = random.choice(customers)
            # Only assign estimate if available and randomly decide to use one
            estimate = None
            if available_estimates and random.choice([True, False, False]):  # 1/3 chance
                estimate = available_estimates.pop(0)  # Remove from available list

            ProjectCard.objects.create(
                title=f"Print Project {i+1}",
                description=f"Print and design project for {customer.name}",
                department="print_design",
                status=random.choice(print_statuses),
                priority=random.choice(["low", "medium", "high", "urgent"]),
                assigned_to=random.choice(users),
                print_customer=customer,
                print_estimate=estimate,
                sla_hours=random.choice([24, 48, 72, 168]),  # 1-7 days
                sla_due_date=timezone.now() + timedelta(hours=random.choice([24, 48, 72, 168])),
                sla_breached=(random.choice([True, False]) if random.random() < 0.15 else False),
                sort_order=i,
                created_by=random.choice(users),
            )

    def create_installations(self):
        """Create installation schedules"""
        self.stdout.write("Creating installations...")

        project_cards = list(ProjectCard.objects.filter(department="print_design"))
        estimates = list(PrintEstimate.objects.all())
        users = list(User.objects.all())

        install_types = ["onsite", "shop", "mobile", "delivery"]
        statuses = [
            "scheduled",
            "confirmed",
            "team_dispatched",
            "on_site",
            "in_progress",
            "completed",
        ]

        for i in range(6):
            project_card = random.choice(project_cards) if project_cards else None

            scheduled_date = timezone.now() + timedelta(days=random.randint(1, 14))

            installation = InstallationSchedule.objects.create(
                project_card=project_card,
                install_type=random.choice(install_types),
                status=random.choice(statuses),
                scheduled_date=scheduled_date,
                estimated_duration=timedelta(hours=random.randint(2, 8)),
                install_address=f"{random.randint(100, 9999)} Business Ave, Albuquerque, NM 87109",
                special_instructions="Handle with care, customer will be on-site",
                equipment_needed="Ladder, drill, measuring tape",
                primary_contact="John Doe",
                contact_phone="(575) 555-0123",
                created_by=random.choice(users),
            )

            # Add team members
            team_size = random.randint(1, 3)
            team_members = random.sample(users, min(team_size, len(users)))
            installation.technician_team.set(team_members)
            # Add team members
            team_size = random.randint(1, 3)
            team_members = random.sample(users, min(team_size, len(users)))
            installation.technician_team.set(team_members)
