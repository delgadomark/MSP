from django.contrib import admin

from .models import CustomerInfo, SLALevel, Ticket, TicketAttachment, TicketNote


class TicketNoteInline(admin.TabularInline):
    """Inline for adding notes to tickets"""

    model = TicketNote
    extra = 1
    fields = ("note", "is_internal", "author")
    readonly_fields = ("author",)


class TicketAttachmentInline(admin.TabularInline):
    """Inline for adding attachments to tickets"""

    model = TicketAttachment
    extra = 1
    fields = ("file", "filename", "uploaded_by")
    readonly_fields = ("uploaded_by",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin interface for managing tickets"""

    list_display = (
        "ticket_number",
        "title",
        "customer_name",
        "priority",
        "status",
        "assigned_to",
        "created_at",
        "is_response_overdue",
        "is_resolution_overdue",
    )
    list_filter = ("status", "priority", "category", "assigned_to", "created_at")
    search_fields = (
        "ticket_number",
        "title",
        "customer_name",
        "customer_email",
        "description",
    )
    readonly_fields = (
        "ticket_number",
        "created_at",
        "updated_at",
        "response_due",
        "resolution_due",
    )
    inlines = [TicketNoteInline, TicketAttachmentInline]

    fieldsets = (
        (
            "Ticket Information",
            {
                "fields": (
                    "ticket_number",
                    "title",
                    "description",
                    "category",
                    "priority",
                    "status",
                )
            },
        ),
        (
            "Customer Information",
            {"fields": ("customer_name", "customer_email", "customer_phone")},
        ),
        ("Assignment", {"fields": ("assigned_to", "created_by")}),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "first_response_at",
                    "resolved_at",
                    "closed_at",
                )
            },
        ),
        (
            "SLA Information",
            {"fields": ("response_due", "resolution_due"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new ticket
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CustomerInfo)
class CustomerInfoAdmin(admin.ModelAdmin):
    """Admin interface for managing customer information"""

    list_display = (
        "customer_name",
        "customer_email",
        "company",
        "computer_make",
        "computer_model",
        "updated_at",
    )
    search_fields = (
        "customer_name",
        "customer_email",
        "company",
        "computer_make",
        "computer_model",
    )
    list_filter = ("computer_make", "operating_system", "created_at")

    fieldsets = (
        (
            "Contact Information",
            {"fields": ("customer_name", "customer_email", "company", "phone")},
        ),
        (
            "Computer Information",
            {
                "fields": (
                    "computer_make",
                    "computer_model",
                    "operating_system",
                    "os_version",
                    "serial_number",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(SLALevel)
class SLALevelAdmin(admin.ModelAdmin):
    """Admin interface for managing SLA levels"""

    list_display = ("priority", "response_time_hours", "resolution_time_hours")
    list_editable = ("response_time_hours", "resolution_time_hours")


@admin.register(TicketNote)
class TicketNoteAdmin(admin.ModelAdmin):
    """Admin interface for managing ticket notes"""

    list_display = ("ticket", "author", "is_internal", "created_at")
    list_filter = ("is_internal", "created_at", "author")
    search_fields = ("ticket__ticket_number", "note", "author__username")
    readonly_fields = ("created_at",)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    """Admin interface for managing ticket attachments"""

    list_display = ("ticket", "filename", "uploaded_by", "uploaded_at")
    list_filter = ("uploaded_at", "uploaded_by")
    search_fields = ("ticket__ticket_number", "filename")
    readonly_fields = ("uploaded_at",)
