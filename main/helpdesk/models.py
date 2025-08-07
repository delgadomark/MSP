from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Priority(models.TextChoices):
    """Priority levels for support tickets"""

    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Status(models.TextChoices):
    """Status choices for tickets"""

    NEW = "new", "New"
    ASSIGNED = "assigned", "Assigned"
    IN_PROGRESS = "in_progress", "In Progress"
    PENDING_CUSTOMER = "pending_customer", "Pending Customer"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class Category(models.TextChoices):
    """Categories for support tickets"""

    TECHNICAL = "technical", "Technical Issue"
    ACCOUNT = "account", "Account Problem"
    BILLING = "billing", "Billing Question"
    FEATURE = "feature", "Feature Request"
    HARDWARE = "hardware", "Hardware Issue"
    SOFTWARE = "software", "Software Issue"
    NETWORK = "network", "Network Issue"
    OTHER = "other", "Other"


class SLALevel(models.Model):
    """SLA levels for different priorities"""

    priority = models.CharField(max_length=10, choices=Priority.choices, unique=True)
    response_time_hours = models.IntegerField(help_text="Hours to respond")
    resolution_time_hours = models.IntegerField(help_text="Hours to resolve")

    def __str__(self):
        return (
            f"{self.get_priority_display()} - {self.response_time_hours}h response,"
            f" {self.resolution_time_hours}h resolution"
        )


class Ticket(models.Model):
    """Support ticket model"""

    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Customer information
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)

    # Categorization
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tickets",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # SLA tracking
    response_due = models.DateTimeField(null=True, blank=True)
    resolution_due = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number
            last_ticket = Ticket.objects.order_by("-id").first()
            if last_ticket:
                last_number = int(last_ticket.ticket_number.split("-")[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.ticket_number = f"TK-{new_number:06d}"

        # Set created_at if not set (for new objects)
        if not self.created_at:
            self.created_at = timezone.now()

        # Set SLA times if not set
        if not self.response_due or not self.resolution_due:
            try:
                sla = SLALevel.objects.get(priority=self.priority)
                if not self.response_due:
                    self.response_due = self.created_at + timedelta(hours=sla.response_time_hours)
                if not self.resolution_due:
                    self.resolution_due = self.created_at + timedelta(
                        hours=sla.resolution_time_hours
                    )
            except SLALevel.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    @property
    def is_response_overdue(self):
        """Check if response is overdue"""
        if self.first_response_at or not self.response_due:
            return False
        return timezone.now() > self.response_due

    @property
    def is_resolution_overdue(self):
        """Check if resolution is overdue"""
        if self.resolved_at or not self.resolution_due:
            return False
        return timezone.now() > self.resolution_due

    @property
    def time_to_response(self):
        """Time until response is due or overdue"""
        if self.first_response_at or not self.response_due:
            return None
        return self.response_due - timezone.now()

    @property
    def time_to_resolution(self):
        """Time until resolution is due or overdue"""
        if self.resolved_at or not self.resolution_due:
            return None
        return self.resolution_due - timezone.now()


class CustomerInfo(models.Model):
    """Customer computer and contact information"""

    customer_email = models.EmailField(unique=True)
    customer_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # Computer information
    computer_make = models.CharField(max_length=50, blank=True)
    computer_model = models.CharField(max_length=50, blank=True)
    operating_system = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)

    # Additional info
    notes = models.TextField(blank=True, help_text="General notes about customer's setup")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_name} ({self.customer_email})"


class TicketNote(models.Model):
    """Notes added to tickets"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    is_internal = models.BooleanField(
        default=False, help_text="Internal notes not visible to customer"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note for {self.ticket.ticket_number} by {self.author.username}"


class TicketAttachment(models.Model):
    """File attachments for tickets"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="ticket_attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} - {self.ticket.ticket_number}"
