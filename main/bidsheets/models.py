from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class CompanyInfo(models.Model):
    """Company information for bid sheets"""

    name = models.CharField(max_length=200, default="Blue Line Technology")
    address = models.TextField(default="814 E. 10th Street\nAlamogordo, NM 88310")
    phone = models.CharField(max_length=20, default="575-479-7470")
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)

    # Terms and conditions
    default_terms = models.TextField(
        default=(
            "Payment is due within 30 days of invoice date. "
            "50% deposit required before work begins. "
            "Final payment due upon completion."
        )
    )

    # Standard exclusions
    default_exclusions = models.TextField(
        default=(
            "Permits and licensing fees\n"
            "Electrical work requiring licensed electrician\n"
            "Structural modifications\n"
            "Unforeseen complications or changes to scope"
        )
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Information"
        verbose_name_plural = "Company Information"

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    """Categories for services offered"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class ServiceItem(models.Model):
    """Standard service items with default pricing"""

    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    default_unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    unit_type = models.CharField(
        max_length=50,
        default="each",
        help_text="e.g., 'each', 'hour', 'sq ft', 'linear ft'",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__sort_order", "category__name", "name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Customer(models.Model):
    """Customer information for bid sheets"""

    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        if self.company:
            return f"{self.name} ({self.company})"
        return self.name


class BidSheet(models.Model):
    """Main bid sheet model"""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    bid_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="bids")

    # Project details
    project_description = models.TextField()
    project_address = models.TextField(blank=True)

    # Bid details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    valid_until = models.DateField()

    # Financial
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False
    )

    # Custom terms and exclusions
    custom_terms = models.TextField(blank=True)
    custom_exclusions = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_bids")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bid_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.bid_number:
            self._generate_bid_number()

        # Set sent_at when status changes to sent
        if self.status == "sent" and not self.sent_at:
            self.sent_at = timezone.now()

        # Save first to ensure we have a primary key
        super().save(*args, **kwargs)

        # Calculate totals after saving
        self._calculate_totals()

        # Save again if totals changed
        if any(
            getattr(self, field, None)
            for field in ["subtotal", "discount_amount", "tax_amount", "total_amount"]
        ):
            super().save(
                update_fields=[
                    "subtotal",
                    "discount_amount",
                    "tax_amount",
                    "total_amount",
                ]
            )

    def _generate_bid_number(self):
        """Generate unique bid number"""
        last_bid = BidSheet.objects.order_by("-id").first()
        if last_bid:
            last_number = int(last_bid.bid_number.split("-")[1])
            new_number = last_number + 1
        else:
            new_number = 1
        self.bid_number = f"BID-{new_number:06d}"

    def _calculate_totals(self):
        """Calculate bid totals"""
        # Only calculate if we have a primary key (object is saved)
        if not self.pk:
            return

        # Calculate subtotal from bid items
        items_total = sum(item.total_price for item in self.items.all())
        self.subtotal = items_total

        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (self.subtotal * self.discount_percentage / 100).quantize(
                Decimal("0.01")
            )
        else:
            self.discount_amount = Decimal("0.00")

        # Calculate tax on discounted amount
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_percentage > 0:
            self.tax_amount = (taxable_amount * self.tax_percentage / 100).quantize(
                Decimal("0.01")
            )
        else:
            self.tax_amount = Decimal("0.00")

        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount

    def recalculate_totals(self):
        """Public method to recalculate totals"""
        self._calculate_totals()
        self.save(update_fields=["subtotal", "discount_amount", "tax_amount", "total_amount"])

    @property
    def is_expired(self):
        """Check if bid has expired"""
        return timezone.now().date() > self.valid_until

    @property
    def company_info(self):
        """Get company information"""
        return CompanyInfo.objects.first()


class BidItem(models.Model):
    """Individual items on a bid sheet"""

    bid = models.ForeignKey(BidSheet, on_delete=models.CASCADE, related_name="items")
    service_item = models.ForeignKey(ServiceItem, on_delete=models.SET_NULL, null=True, blank=True)

    # Item details (can override service item or be custom)
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    unit_type = models.CharField(max_length=50, default="each")

    # Calculated field
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = (self.quantity * self.unit_price).quantize(Decimal("0.01"))

        # If service_item is set and description is empty, use service item description
        if self.service_item and not self.description:
            self.description = self.service_item.name

        super().save(*args, **kwargs)

        # Recalculate bid totals
        self.bid.recalculate_totals()

    def delete(self, *args, **kwargs):
        bid = self.bid
        super().delete(*args, **kwargs)
        # Recalculate bid totals after deletion
        bid.recalculate_totals()

    def __str__(self):
        return f"{self.bid.bid_number} - {self.description}"


class BidEmailLog(models.Model):
    """Log of emails sent for bid sheets"""

    bid = models.ForeignKey(BidSheet, on_delete=models.CASCADE, related_name="email_logs")
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Email for {self.bid.bid_number} to {self.recipient_email}"
        return f"Email for {self.bid.bid_number} to {self.recipient_email}"
