from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BidEmailLog,
    BidItem,
    BidSheet,
    CompanyInfo,
    Customer,
    ServiceCategory,
    ServiceItem,
)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "updated_at"]
    fields = [
        "name",
        "address",
        "phone",
        "email",
        "website",
        "logo",
        "default_terms",
        "default_exclusions",
    ]

    def has_add_permission(self, request):
        # Only allow one company info record
        return not CompanyInfo.objects.exists()


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "sort_order", "item_count"]
    list_editable = ["sort_order"]
    ordering = ["sort_order", "name"]

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Items"


class ServiceItemInline(admin.TabularInline):
    model = ServiceItem
    extra = 0
    fields = ["name", "description", "default_unit_price", "unit_type", "is_active"]


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "default_unit_price", "unit_type", "is_active"]
    list_filter = ["category", "is_active", "unit_type"]
    search_fields = ["name", "description"]
    list_editable = ["default_unit_price", "is_active"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "email", "phone", "bid_count"]
    search_fields = ["name", "company", "email"]

    def bid_count(self, obj):
        return obj.bids.count()

    bid_count.short_description = "Bids"


class BidItemInline(admin.TabularInline):
    model = BidItem
    extra = 1
    fields = [
        "service_item",
        "description",
        "quantity",
        "unit_price",
        "unit_type",
        "sort_order",
    ]
    readonly_fields = ["total_price"]


class BidEmailLogInline(admin.TabularInline):
    model = BidEmailLog
    extra = 0
    readonly_fields = ["sent_at", "sent_by", "success"]
    fields = ["recipient_email", "subject", "sent_at", "sent_by", "success"]


@admin.register(BidSheet)
class BidSheetAdmin(admin.ModelAdmin):
    list_display = [
        "bid_number",
        "title",
        "customer",
        "status",
        "total_amount",
        "valid_until",
        "is_expired_display",
        "created_at",
    ]
    list_filter = ["status", "created_at", "valid_until"]
    search_fields = ["bid_number", "title", "customer__name", "customer__company"]
    readonly_fields = [
        "bid_number",
        "subtotal",
        "discount_amount",
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
        "sent_at",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("bid_number", "title", "customer", "status")},
        ),
        (
            "Project Details",
            {"fields": ("project_description", "project_address", "valid_until")},
        ),
        (
            "Financial",
            {
                "fields": (
                    "subtotal",
                    "discount_percentage",
                    "discount_amount",
                    "tax_percentage",
                    "tax_amount",
                    "total_amount",
                )
            },
        ),
        (
            "Terms & Conditions",
            {
                "fields": ("custom_terms", "custom_exclusions", "notes"),
                "classes": ("collapse",),
            },
        ),
        (
            "Tracking",
            {
                "fields": ("created_by", "created_at", "updated_at", "sent_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [BidItemInline, BidEmailLogInline]

    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return "Valid"

    is_expired_display.short_description = "Status"

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BidEmailLog)
class BidEmailLogAdmin(admin.ModelAdmin):
    list_display = [
        "bid",
        "recipient_email",
        "subject",
        "sent_at",
        "sent_by",
        "success",
    ]
    list_filter = ["success", "sent_at"]
    readonly_fields = ["sent_at"]
