from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "get_access_level",
        "primary_department",
        "can_access_technology",
        "can_access_print_design",
        "created_at",
    ]
    list_filter = [
        "primary_department",
        "can_access_technology",
        "can_access_print_design",
        "created_at",
    ]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "employee_id",
    ]
    list_editable = [
        "can_access_technology",
        "can_access_print_design",
        "primary_department",
    ]

    fieldsets = (
        ("User Information", {"fields": ("user", "employee_id", "phone")}),
        (
            "Department Access",
            {
                "fields": (
                    "primary_department",
                    "can_access_technology",
                    "can_access_print_design",
                ),
                "description": (
                    "Set department access permissions. Master users have access to both"
                    " departments."
                ),
            },
        ),
    )

    def get_access_level(self, obj):
        return obj.get_access_level()

    get_access_level.short_description = "Access Level"
    get_access_level.short_description = "Access Level"
