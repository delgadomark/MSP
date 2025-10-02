from django.contrib import admin

from .models import (
    PrintCustomer,
    PrintEstimate,
    PrintEstimateItem,
    PrintServiceCategory,
    PrintServiceItem,
    ProductSheet,
)


@admin.register(PrintCustomer)
class PrintCustomerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "company",
        "customer_type",
        "email",
        "phone",
        "city",
        "state",
        "created_at",
    ]
    list_filter = [
        "customer_type",
        "tax_exempt",
        "credit_approved",
        "state",
        "created_at",
    ]
    search_fields = ["name", "company", "email", "phone", "address"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "company", "customer_type", "email", "phone")},
        ),
        ("Address", {"fields": ("address", "city", "state", "zip_code")}),
        ("Preferences", {"fields": ("preferred_contact_method",)}),
        (
            "Financial",
            {
                "fields": (
                    "tax_exempt",
                    "tax_exempt_number",
                    "credit_approved",
                    "credit_limit",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PrintServiceCategory)
class PrintServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]


class PrintServiceItemInline(admin.TabularInline):
    model = PrintServiceItem
    extra = 0
    fields = ["name", "unit_type", "base_price", "is_active"]


@admin.register(PrintServiceItem)
class PrintServiceItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "unit_type",
        "base_price",
        "paper_type",
        "finish_type",
        "is_active",
    ]
    list_filter = [
        "category",
        "unit_type",
        "paper_type",
        "finish_type",
        "is_active",
        "requires_design",
    ]
    search_fields = ["name", "description"]
    list_editable = ["is_active"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "category",
                    "name",
                    "description",
                    "unit_type",
                    "base_price",
                    "is_active",
                )
            },
        ),
        (
            "Print Specifications",
            {
                "fields": (
                    "paper_type",
                    "finish_type",
                    "min_quantity",
                    "max_quantity",
                    "setup_fee",
                )
            },
        ),
        (
            "Pricing Tiers",
            {
                "fields": (
                    ("tier_1_qty", "tier_1_price"),
                    ("tier_2_qty", "tier_2_price"),
                    ("tier_3_qty", "tier_3_price"),
                )
            },
        ),
        ("Production", {"fields": ("requires_design", "production_time_days")}),
    )


class PrintEstimateItemInline(admin.TabularInline):
    model = PrintEstimateItem
    extra = 1
    fields = ["description", "quantity", "unit_price", "total_price", "setup_fee"]
    readonly_fields = ["total_price"]


@admin.register(PrintEstimate)
class PrintEstimateAdmin(admin.ModelAdmin):
    list_display = [
        "estimate_number",
        "customer",
        "title",
        "status",
        "total_amount",
        "created_date",
        "valid_until",
    ]
    list_filter = ["status", "created_date", "valid_until"]
    search_fields = ["estimate_number", "customer__name", "customer__company", "title"]
    readonly_fields = [
        "estimate_number",
        "created_at",
        "updated_at",
        "subtotal",
        "discount_amount",
        "tax_amount",
        "total_amount",
    ]
    inlines = [PrintEstimateItemInline]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "estimate_number",
                    "customer",
                    "title",
                    "description",
                    "status",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_date",
                    "valid_until",
                    "production_start_date",
                    "estimated_completion_date",
                )
            },
        ),
        ("Project Details", {"fields": ("project_address", "special_instructions")}),
        (
            "Pricing",
            {
                "fields": (
                    "subtotal",
                    ("discount_percentage", "discount_amount"),
                    ("tax_percentage", "tax_amount"),
                    "total_amount",
                )
            },
        ),
        ("Terms", {"fields": ("payment_terms", "warranty_terms", "delivery_terms")}),
        (
            "System Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ProductSheet)
class ProductSheetAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "product_type",
        "base_price",
        "min_quantity",
        "production_time_days",
        "is_active",
        "featured",
        "sort_order",
    ]
    list_filter = [
        "product_type",
        "is_active",
        "featured",
        "setup_required",
        "design_included",
    ]
    search_fields = ["name", "description"]
    list_editable = ["is_active", "featured", "sort_order"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "product_type",
                    "description",
                    "is_active",
                    "featured",
                    "sort_order",
                )
            },
        ),
        (
            "Specifications",
            {
                "fields": (
                    "available_sizes",
                    "available_papers",
                    "available_finishes",
                    "color_options",
                )
            },
        ),
        ("Pricing", {"fields": ("base_price", "price_notes")}),
        (
            "Production",
            {
                "fields": (
                    "min_quantity",
                    "production_time_days",
                    "setup_required",
                    "design_included",
                )
            },
        ),
        ("Images", {"fields": ("image", "sample_image")}),
        (
            "System Information",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
