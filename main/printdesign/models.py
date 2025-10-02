import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class PrintCustomer(models.Model):
    """Separate customer model for Print & Design department"""

    CUSTOMER_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("business", "Business"),
        ("non_profit", "Non-Profit"),
        ("government", "Government"),
    ]

    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    customer_type = models.CharField(
        max_length=20, choices=CUSTOMER_TYPE_CHOICES, default="business"
    )
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10)

    # Print-specific fields
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("phone", "Phone"),
            ("text", "Text Message"),
        ],
        default="email",
    )

    tax_exempt = models.BooleanField(default=False)
    tax_exempt_number = models.CharField(max_length=50, blank=True)
    credit_approved = models.BooleanField(default=False)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="print_customers_created",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Print Customer"
        verbose_name_plural = "Print Customers"

    def __str__(self):
        return f"{self.name} - {self.company}" if self.company else self.name

    def get_absolute_url(self):
        return reverse("print_customer_detail", kwargs={"pk": self.pk})


class PrintServiceCategory(models.Model):
    """Categories for print services"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Print Service Category"
        verbose_name_plural = "Print Service Categories"

    def __str__(self):
        return self.name


class PrintServiceItem(models.Model):
    """Print and design service items"""

    UNIT_CHOICES = [
        ("each", "Each"),
        ("sqft", "Square Foot"),
        ("linft", "Linear Foot"),
        ("sheet", "Sheet"),
        ("hour", "Hour"),
        ("day", "Day"),
        ("project", "Project"),
    ]

    PAPER_TYPE_CHOICES = [
        ("standard", "Standard Paper"),
        ("premium", "Premium Paper"),
        ("cardstock", "Cardstock"),
        ("vinyl", "Vinyl"),
        ("canvas", "Canvas"),
        ("fabric", "Fabric"),
        ("metal", "Metal"),
        ("acrylic", "Acrylic"),
        ("foam_board", "Foam Board"),
        ("coroplast", "Coroplast"),
        ("banner", "Banner Material"),
    ]

    FINISH_CHOICES = [
        ("none", "No Finish"),
        ("gloss", "Gloss"),
        ("matte", "Matte"),
        ("satin", "Satin"),
        ("uv_coating", "UV Coating"),
        ("laminated", "Laminated"),
        ("embossed", "Embossed"),
        ("foil_stamped", "Foil Stamped"),
    ]

    category = models.ForeignKey(
        PrintServiceCategory, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES, default="each")
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Print-specific fields
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE_CHOICES, default="standard")
    finish_type = models.CharField(max_length=20, choices=FINISH_CHOICES, default="none")
    min_quantity = models.IntegerField(default=1)
    max_quantity = models.IntegerField(null=True, blank=True)
    setup_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Pricing tiers
    tier_1_qty = models.IntegerField(default=1, help_text="Quantity for tier 1 pricing")
    tier_1_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price per unit for tier 1"
    )
    tier_2_qty = models.IntegerField(
        null=True, blank=True, help_text="Quantity for tier 2 pricing"
    )
    tier_2_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tier_3_qty = models.IntegerField(
        null=True, blank=True, help_text="Quantity for tier 3 pricing"
    )
    tier_3_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    requires_design = models.BooleanField(default=False)
    production_time_days = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "Print Service Item"
        verbose_name_plural = "Print Service Items"

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def get_price_for_quantity(self, quantity):
        """Calculate price based on quantity tiers"""
        if self.tier_3_qty and quantity >= self.tier_3_qty:
            return self.tier_3_price
        elif self.tier_2_qty and quantity >= self.tier_2_qty:
            return self.tier_2_price
        else:
            return self.tier_1_price


class PrintEstimate(models.Model):
    """Print and design estimates"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent to Customer"),
        ("approved", "Approved"),
        ("declined", "Declined"),
        ("expired", "Expired"),
        ("in_production", "In Production"),
        ("completed", "Completed"),
    ]

    estimate_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(PrintCustomer, on_delete=models.CASCADE, related_name="estimates")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Dates
    created_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    production_start_date = models.DateField(null=True, blank=True)
    estimated_completion_date = models.DateField(null=True, blank=True)

    # Project details
    project_address = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Terms
    payment_terms = models.CharField(max_length=100, default="Net 30")
    warranty_terms = models.TextField(blank=True)
    delivery_terms = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="print_estimates_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_date"]
        verbose_name = "Print Estimate"
        verbose_name_plural = "Print Estimates"

    def __str__(self):
        return f"{self.estimate_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.estimate_number:
            self.estimate_number = self.generate_estimate_number()

        if not self.valid_until:
            self.valid_until = date.today() + timedelta(days=30)

        super().save(*args, **kwargs)

    def generate_estimate_number(self):
        """Generate unique estimate number"""
        today = date.today()
        prefix = f"PE{today.strftime('%Y%m')}"

        last_estimate = (
            PrintEstimate.objects.filter(estimate_number__startswith=prefix)
            .order_by("-estimate_number")
            .first()
        )

        if last_estimate:
            last_number = int(last_estimate.estimate_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"

    def recalculate_totals(self):
        """Recalculate estimate totals"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.discount_amount = self.subtotal * (self.discount_percentage / Decimal("100"))
        after_discount = self.subtotal - self.discount_amount
        self.tax_amount = after_discount * (self.tax_percentage / Decimal("100"))
        self.total_amount = after_discount + self.tax_amount
        self.save()

    def get_absolute_url(self):
        return reverse("print_estimate_detail", kwargs={"pk": self.pk})


class PrintEstimateItem(models.Model):
    """Individual items in a print estimate"""

    estimate = models.ForeignKey(PrintEstimate, on_delete=models.CASCADE, related_name="items")
    service_item = models.ForeignKey(
        PrintServiceItem, on_delete=models.CASCADE, null=True, blank=True
    )

    # Item details
    description = models.TextField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_type = models.CharField(max_length=20, default="each")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    # Print-specific details
    dimensions = models.CharField(max_length=100, blank=True, help_text="e.g., 24x36 inches")
    paper_type = models.CharField(max_length=100, blank=True)
    finish_type = models.CharField(max_length=100, blank=True)
    colors = models.CharField(
        max_length=100, blank=True, help_text="e.g., 4/4 (full color both sides)"
    )

    # Production details
    setup_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    production_notes = models.TextField(blank=True)
    requires_design = models.BooleanField(default=False)
    design_time_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Print Estimate Item"
        verbose_name_plural = "Print Estimate Items"

    def __str__(self):
        return f"{self.estimate.estimate_number} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        self.total_price = (self.quantity * self.unit_price) + self.setup_fee
        super().save(*args, **kwargs)


class ProductSheet(models.Model):
    """Product catalog/inventory for print services"""

    PRODUCT_TYPE_CHOICES = [
        ("business_cards", "Business Cards"),
        ("brochures", "Brochures"),
        ("flyers", "Flyers"),
        ("banners", "Banners"),
        ("signs", "Signs"),
        ("vehicle_graphics", "Vehicle Graphics"),
        ("promotional", "Promotional Items"),
        ("custom", "Custom Products"),
    ]

    name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=30, choices=PRODUCT_TYPE_CHOICES)
    description = models.TextField()

    # Specifications
    available_sizes = models.TextField(help_text="List available sizes, one per line")
    available_papers = models.TextField(help_text="List available paper types, one per line")
    available_finishes = models.TextField(help_text="List available finishes, one per line")
    color_options = models.TextField(help_text="Color options available")

    # Pricing information
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_notes = models.TextField(blank=True, help_text="Additional pricing information")

    # Production details
    min_quantity = models.IntegerField(default=1)
    production_time_days = models.IntegerField(default=1)
    setup_required = models.BooleanField(default=False)
    design_included = models.BooleanField(default=False)

    # Images
    image = models.ImageField(upload_to="product_images/", blank=True)
    sample_image = models.ImageField(upload_to="product_samples/", blank=True)

    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["product_type", "sort_order", "name"]
        verbose_name = "Product Sheet"
        verbose_name_plural = "Product Sheets"

    def __str__(self):
        return f"{self.get_product_type_display()} - {self.name}"

    def get_absolute_url(self):
        return reverse("product_sheet_detail", kwargs={"pk": self.pk})
        return reverse("product_sheet_detail", kwargs={"pk": self.pk})
