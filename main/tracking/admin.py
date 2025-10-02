from django.contrib import admin

from .models import InstallationSchedule, ProjectCard, Vehicle, VehicleDropOff


@admin.register(ProjectCard)
class ProjectCardAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "department",
        "status",
        "priority",
        "assigned_to",
        "created_at",
        "sla_due_date",
    ]
    list_filter = ["department", "status", "priority", "created_at"]
    search_fields = ["title", "description", "assigned_to__username"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "description", "department", "status", "priority")},
        ),
        ("Assignment", {"fields": ("assigned_to",)}),
        ("Customer Information", {"fields": ("tech_customer", "print_customer")}),
        ("Dates", {"fields": ("sla_due_date", "started_at", "completed_at")}),
        (
            "SLA Tracking",
            {
                "fields": ("sla_hours", "sla_breached", "sla_breach_reason"),
                "classes": ("collapse",),
            },
        ),
        (
            "Attachments & Links",
            {"fields": ("bid_sheet", "print_estimate"), "classes": ("collapse",)},
        ),
        (
            "System Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("assigned_to", "tech_customer", "print_customer", "created_by")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["license_plate", "make", "model", "year", "vin"]
    list_filter = ["make", "year"]
    search_fields = ["make", "model", "license_plate", "vin"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Vehicle Information",
            {"fields": ("make", "model", "year", "color", "license_plate", "vin")},
        ),
        ("Customer Relationships", {"fields": ("tech_customer", "print_customer")}),
        ("Notes", {"fields": ("notes",)}),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(VehicleDropOff)
class VehicleDropOffAdmin(admin.ModelAdmin):
    list_display = [
        "vehicle",
        "project_card",
        "scheduled_drop_off",
        "status",
        "technician_assigned",
    ]
    list_filter = ["status", "scheduled_drop_off", "technician_assigned"]
    search_fields = ["vehicle__license_plate", "work_description", "drop_off_contact"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("vehicle", "project_card")}),
        (
            "Schedule",
            {
                "fields": (
                    "scheduled_drop_off",
                    "actual_drop_off",
                    "expected_completion",
                    "actual_completion",
                )
            },
        ),
        (
            "Location & Assignment",
            {
                "fields": (
                    "drop_off_location",
                    "bay_number",
                    "technician_assigned",
                    "status",
                )
            },
        ),
        (
            "Work Details",
            {"fields": ("work_description", "customer_notes", "internal_notes")},
        ),
        ("Contact Information", {"fields": ("drop_off_contact", "pickup_contact")}),
        (
            "System Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(InstallationSchedule)
class InstallationScheduleAdmin(admin.ModelAdmin):
    list_display = ["project_card", "install_type", "scheduled_date", "status"]
    list_filter = ["install_type", "status", "scheduled_date"]
    search_fields = ["project_card__title", "primary_contact", "install_address"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("project_card", "install_type", "status")}),
        (
            "Schedule",
            {
                "fields": (
                    "scheduled_date",
                    "estimated_duration",
                    "actual_start",
                    "actual_end",
                )
            },
        ),
        (
            "Location & Team",
            {
                "fields": (
                    "install_address",
                    "special_instructions",
                    "equipment_needed",
                    "technician_team",
                )
            },
        ),
        (
            "Contact Information",
            {"fields": ("primary_contact", "contact_phone", "backup_contact")},
        ),
        (
            "Completion",
            {"fields": ("completion_notes", "client_signature", "photos_taken")},
        ),
        (
            "System Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
