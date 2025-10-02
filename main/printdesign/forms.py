from django import forms
from django.core.exceptions import ValidationError

from .models import (
    PrintCustomer,
    PrintEstimate,
    PrintEstimateItem,
    PrintServiceCategory,
    PrintServiceItem,
    ProductSheet,
)


class PrintCustomerForm(forms.ModelForm):
    class Meta:
        model = PrintCustomer
        fields = [
            "name",
            "company",
            "customer_type",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "zip_code",
            "preferred_contact_method",
            "tax_exempt",
            "tax_exempt_number",
            "credit_approved",
            "credit_limit",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "customer_type": forms.Select(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.Select(attrs={"class": "form-control"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_contact_method": forms.Select(attrs={"class": "form-control"}),
            "tax_exempt_number": forms.TextInput(attrs={"class": "form-control"}),
            "credit_limit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            # Check for duplicate email (excluding current instance if editing)
            qs = PrintCustomer.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A customer with this email already exists.")
        return email


class PrintEstimateForm(forms.ModelForm):
    class Meta:
        model = PrintEstimate
        fields = [
            "customer",
            "title",
            "description",
            "status",
            "valid_until",
            "production_start_date",
            "estimated_completion_date",
            "project_address",
            "special_instructions",
            "discount_percentage",
            "tax_percentage",
            "payment_terms",
            "warranty_terms",
            "delivery_terms",
        ]
        widgets = {
            "customer": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "valid_until": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "production_start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "estimated_completion_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "project_address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "special_instructions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "discount_percentage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "tax_percentage": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "50"}
            ),
            "payment_terms": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "warranty_terms": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "delivery_terms": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        if not self.instance.pk:
            self.fields["tax_percentage"].initial = 8.25  # Default tax rate


class PrintEstimateItemForm(forms.ModelForm):
    class Meta:
        model = PrintEstimateItem
        fields = [
            "description",
            "quantity",
            "unit_price",
            "setup_fee",
            "production_notes",
        ]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "unit_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "setup_fee": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "production_notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class PrintServiceItemForm(forms.ModelForm):
    class Meta:
        model = PrintServiceItem
        fields = [
            "category",
            "name",
            "description",
            "unit_type",
            "base_price",
            "paper_type",
            "finish_type",
            "min_quantity",
            "max_quantity",
            "setup_fee",
            "tier_1_qty",
            "tier_1_price",
            "tier_2_qty",
            "tier_2_price",
            "tier_3_qty",
            "tier_3_price",
            "requires_design",
            "production_time_days",
            "is_active",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "unit_type": forms.Select(attrs={"class": "form-control"}),
            "base_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "paper_type": forms.Select(attrs={"class": "form-control"}),
            "finish_type": forms.Select(attrs={"class": "form-control"}),
            "min_quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "max_quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "setup_fee": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "tier_1_qty": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "tier_1_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "tier_2_qty": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "tier_2_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "tier_3_qty": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "tier_3_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "production_time_days": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }


class ProductSheetForm(forms.ModelForm):
    class Meta:
        model = ProductSheet
        fields = [
            "name",
            "product_type",
            "description",
            "available_sizes",
            "available_papers",
            "available_finishes",
            "color_options",
            "base_price",
            "price_notes",
            "min_quantity",
            "production_time_days",
            "setup_required",
            "design_included",
            "image",
            "sample_image",
            "is_active",
            "featured",
            "sort_order",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "product_type": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "available_sizes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter available sizes, one per line",
                }
            ),
            "available_papers": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter available paper types, one per line",
                }
            ),
            "available_finishes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter available finishes, one per line",
                }
            ),
            "color_options": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Enter color options",
                }
            ),
            "base_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "price_notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "min_quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "production_time_days": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "sample_image": forms.FileInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class EmailEstimateForm(forms.Form):
    """Form for emailing estimates to customers"""

    recipient_email = forms.EmailField(
        label="Recipient Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "customer@example.com"}
        ),
    )
    subject = forms.CharField(
        label="Subject",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email subject"}),
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Email message...",
            }
        ),
    )
    include_pdf = forms.BooleanField(
        label="Include PDF attachment",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    copy_to_sender = forms.BooleanField(
        label="Send copy to me",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class CustomerSearchForm(forms.Form):
    """Customer search form"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search by name, company, email, or phone...",
            }
        ),
    )
    customer_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + PrintCustomer.CUSTOMER_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
    )
