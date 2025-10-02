import uuid
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone


class ProjectCard(models.Model):
    """Kanban/Jira-style project tracking cards"""

    DEPARTMENT_CHOICES = [
        ("technology", "Technology"),
        ("print_design", "Print & Design"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    STATUS_CHOICES = [
        # Technology statuses
        ("tech_backlog", "Backlog"),
        ("tech_in_progress", "In Progress"),
        ("tech_awaiting_client", "Awaiting Client"),
        ("tech_testing", "Testing"),
        ("tech_completed", "Completed"),
        # Print & Design statuses
        ("print_design_brief", "Design Brief"),
        ("print_design_phase", "Design Phase"),
        ("print_client_approval", "Client Approval"),
        ("print_production", "Production"),
        ("print_quality_check", "Quality Check"),
        ("print_delivered", "Delivered"),
        # Common statuses
        ("on_hold", "On Hold"),
        ("cancelled", "Cancelled"),
    ]

    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")

    # Relationships
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cards",
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_cards"
    )

    # Technology relationships
    bid_sheet = models.OneToOneField(
        "bidsheets.BidSheet",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="project_card",
    )
    tech_customer = models.ForeignKey(
        "bidsheets.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tech_project_cards",
    )

    # Print & Design relationships
    print_estimate = models.OneToOneField(
        "printdesign.PrintEstimate",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="project_card",
    )
    print_customer = models.ForeignKey(
        "printdesign.PrintCustomer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="print_project_cards",
    )

    # Time tracking
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    billable_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # SLA tracking
    sla_due_date = models.DateTimeField(null=True, blank=True)
    sla_hours = models.IntegerField(default=24, help_text="SLA in hours")
    sla_breached = models.BooleanField(default=False)
    sla_breach_reason = models.TextField(blank=True)

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Position for drag & drop
    sort_order = models.IntegerField(default=0)

    # Progress tracking
    progress_percentage = models.IntegerField(default=0, help_text="0-100")

    class Meta:
        ordering = ["sort_order", "-priority", "created_at"]
        verbose_name = "Project Card"
        verbose_name_plural = "Project Cards"

    def __str__(self):
        return f"{self.title} ({self.get_department_display()})"

    @property
    def customer_name(self):
        """Get customer name regardless of department"""
        if self.tech_customer:
            return self.tech_customer.name
        elif self.print_customer:
            return self.print_customer.name
        return "No Customer"

    @property
    def is_overdue(self):
        """Check if card is overdue based on SLA"""
        if self.sla_due_date and not self.completed_at:
            return timezone.now() > self.sla_due_date
        return False

    @property
    def time_remaining(self):
        """Calculate time remaining until SLA breach"""
        if self.sla_due_date and not self.completed_at:
            remaining = self.sla_due_date - timezone.now()
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
        return None

    def calculate_sla_due_date(self):
        """Calculate SLA due date based on creation time and SLA hours"""
        if self.created_at and self.sla_hours:
            self.sla_due_date = self.created_at + timedelta(hours=self.sla_hours)

    def save(self, *args, **kwargs):
        if not self.sla_due_date:
            self.calculate_sla_due_date()

        # Check for SLA breach
        if self.is_overdue and not self.sla_breached:
            self.sla_breached = True

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("project_card_detail", kwargs={"pk": self.pk})


class CardComment(models.Model):
    """Comments/activity log for project cards"""

    COMMENT_TYPES = [
        ("comment", "Comment"),
        ("status_change", "Status Change"),
        ("assignment", "Assignment Change"),
        ("time_log", "Time Log"),
        ("file_upload", "File Upload"),
        ("system", "System Update"),
    ]

    card = models.ForeignKey(ProjectCard, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPES, default="comment")
    content = models.TextField()

    # For time logging
    time_spent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    billable = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.card.title} - {self.get_comment_type_display()} by {self.user}"


class CardAttachment(models.Model):
    """File attachments for project cards"""

    card = models.ForeignKey(ProjectCard, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="card_attachments/")
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.card.title} - {self.filename}"


class Vehicle(models.Model):
    """Vehicle information for tracking drop-offs and installations"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("maintenance", "In Maintenance"),
        ("out_of_service", "Out of Service"),
        ("retired", "Retired"),
    ]

    VEHICLE_TYPE_CHOICES = [
        ("truck", "Truck"),
        ("van", "Van"),
        ("car", "Car"),
        ("trailer", "Trailer"),
        ("equipment", "Equipment"),
    ]

    DEPARTMENT_CHOICES = [
        ("technology", "Technology"),
        ("print_design", "Print & Design"),
        ("shared", "Shared"),
    ]

    # Basic vehicle information
    license_plate = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    color = models.CharField(max_length=50)
    vin = models.CharField(max_length=17, unique=True, null=True, blank=True)

    # Vehicle management fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default="truck")
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default="shared")
    current_driver = models.CharField(max_length=100, blank=True)
    current_mileage = models.IntegerField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)

    # Customer relationship (can be either tech or print customer)
    tech_customer = models.ForeignKey(
        "bidsheets.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="vehicles",
    )
    print_customer = models.ForeignKey(
        "printdesign.PrintCustomer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="vehicles",
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["license_plate"]

    def __str__(self):
        return f"{self.license_plate} - {self.year} {self.make} {self.model}"

    @property
    def customer_name(self):
        """Get customer name regardless of type"""
        if self.tech_customer:
            return self.tech_customer.name
        elif self.print_customer:
            return self.print_customer.name
        return "No Customer"


class VehicleDropOff(models.Model):
    """Track vehicle drop-offs for service"""

    DROP_OFF_STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("dropped_off", "Vehicle Dropped Off"),
        ("in_progress", "Work In Progress"),
        ("awaiting_parts", "Awaiting Parts"),
        ("completed", "Work Completed"),
        ("ready_pickup", "Ready for Pickup"),
        ("picked_up", "Picked Up"),
        ("cancelled", "Cancelled"),
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="drop_offs")
    project_card = models.ForeignKey(
        ProjectCard, on_delete=models.CASCADE, related_name="vehicle_drop_offs"
    )

    # Scheduling
    scheduled_drop_off = models.DateTimeField()
    actual_drop_off = models.DateTimeField(null=True, blank=True)
    expected_completion = models.DateTimeField()
    actual_completion = models.DateTimeField(null=True, blank=True)

    # Location and assignment
    drop_off_location = models.CharField(max_length=200, default="Main Shop")
    bay_number = models.CharField(max_length=10, blank=True)
    technician_assigned = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicle_assignments",
    )

    # Status and details
    status = models.CharField(max_length=20, choices=DROP_OFF_STATUS_CHOICES, default="scheduled")
    work_description = models.TextField()
    customer_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Contact information
    drop_off_contact = models.CharField(max_length=100, blank=True)
    pickup_contact = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="vehicle_drop_offs_created",
    )

    class Meta:
        ordering = ["-scheduled_drop_off"]
        verbose_name = "Vehicle Drop-Off"
        verbose_name_plural = "Vehicle Drop-Offs"

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.scheduled_drop_off.strftime('%m/%d/%Y')}"


class InstallationSchedule(models.Model):
    """Schedule and track installations"""

    INSTALL_TYPE_CHOICES = [
        ("onsite", "On-Site Installation"),
        ("shop", "Shop Installation"),
        ("mobile", "Mobile Service"),
        ("delivery", "Delivery Only"),
    ]

    INSTALL_STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("team_dispatched", "Team Dispatched"),
        ("on_site", "On Site"),
        ("in_progress", "Installation In Progress"),
        ("completed", "Installation Complete"),
        ("client_signoff", "Client Sign-Off"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    project_card = models.ForeignKey(
        ProjectCard, on_delete=models.CASCADE, related_name="installations"
    )

    # Installation details
    install_type = models.CharField(max_length=20, choices=INSTALL_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=INSTALL_STATUS_CHOICES, default="scheduled")

    # Scheduling
    scheduled_date = models.DateTimeField()
    estimated_duration = models.DurationField(default=timedelta(hours=2))
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Location and team
    install_address = models.TextField()
    special_instructions = models.TextField(blank=True)
    equipment_needed = models.TextField(blank=True)
    technician_team = models.ManyToManyField(User, related_name="installations", blank=True)

    # Contact information
    primary_contact = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    backup_contact = models.CharField(max_length=100, blank=True)

    # Completion details
    completion_notes = models.TextField(blank=True)
    client_signature = models.CharField(max_length=100, blank=True)
    photos_taken = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="installations_created"
    )

    class Meta:
        ordering = ["scheduled_date"]
        verbose_name = "Installation Schedule"
        verbose_name_plural = "Installation Schedules"

    def __str__(self):
        return f"{self.project_card.title} - {self.scheduled_date.strftime('%m/%d/%Y %I:%M %p')}"

    @property
    def actual_duration(self):
        """Calculate actual installation duration"""
        if self.actual_start and self.actual_end:
            return self.actual_end - self.actual_start
        return None
        return None
