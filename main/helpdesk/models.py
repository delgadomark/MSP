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

    def save(self, *args, **kwargs):  # pylint: disable=too-many-branches
        # Check if this is an existing ticket (has an ID)
        is_new = self.pk is None
        old_status = self._get_old_status(is_new)

        self._generate_ticket_number()
        self._set_creation_time()
        self._handle_status_changes(old_status)
        self._set_sla_times()

        super().save(*args, **kwargs)

    def _get_old_status(self, is_new):
        """Get the old status for change detection"""
        if is_new:
            return None
        try:
            old_ticket = Ticket.objects.get(pk=self.pk)
            return old_ticket.status
        except Ticket.DoesNotExist:
            return None

    def _generate_ticket_number(self):
        """Generate unique ticket number if not set"""
        if not self.ticket_number:
            last_ticket = Ticket.objects.order_by("-id").first()
            if last_ticket:
                last_number = int(last_ticket.ticket_number.split("-")[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.ticket_number = f"TK-{new_number:06d}"

    def _set_creation_time(self):
        """Set created_at if not set (for new objects)"""
        if not self.created_at:
            self.created_at = timezone.now()

    def _handle_status_changes(self, old_status):
        """Handle status changes and SLA tracking"""
        current_time = timezone.now()

        # Set resolved_at when ticket is marked as resolved
        if self.status == Status.RESOLVED and old_status != Status.RESOLVED:
            if not self.resolved_at:
                self.resolved_at = current_time

        # Set closed_at when ticket is marked as closed
        if self.status == Status.CLOSED and old_status != Status.CLOSED:
            if not self.closed_at:
                self.closed_at = current_time
            # Also set resolved_at if not already set
            if not self.resolved_at:
                self.resolved_at = current_time

        # Clear timestamps if status is changed back from resolved/closed
        if self.status not in [Status.RESOLVED, Status.CLOSED]:
            if old_status in [Status.RESOLVED, Status.CLOSED]:
                self.resolved_at = None
                self.closed_at = None

    def _set_sla_times(self):
        """Set SLA times if not set"""
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

    @property
    def response_time_taken(self):
        """Actual time taken to respond (if responded)"""
        if not self.first_response_at or not self.created_at:
            return None
        return self.first_response_at - self.created_at

    @property
    def resolution_time_taken(self):
        """Actual time taken to resolve (if resolved)"""
        if not self.resolved_at or not self.created_at:
            return None
        return self.resolved_at - self.created_at

    @property
    def was_response_sla_met(self):
        """Check if response SLA was met"""
        if not self.first_response_at or not self.response_due:
            return None
        return self.first_response_at <= self.response_due

    @property
    def was_resolution_sla_met(self):
        """Check if resolution SLA was met"""
        if not self.resolved_at or not self.resolution_due:
            return None
        return self.resolved_at <= self.resolution_due

    @property
    def sla_status(self):
        """Overall SLA status for the ticket"""
        if self.status in [Status.RESOLVED, Status.CLOSED]:
            # Ticket is complete, check if SLAs were met
            response_met = self.was_response_sla_met
            resolution_met = self.was_resolution_sla_met

            # If no first response was recorded, consider response SLA as met
            # (this handles cases where tickets are resolved without formal response tracking)
            if response_met is None and self.first_response_at is None:
                response_met = True

            if response_met is False or resolution_met is False:
                return "SLA Missed"
            if response_met is True and resolution_met is True:
                return "SLA Met"
            return "Incomplete Data"

        # Ticket is still open, check if overdue
        if self.is_response_overdue or self.is_resolution_overdue:
            return "Overdue"
        return "On Track"


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
