from django import forms
from django.forms import inlineformset_factory

from .models import BidItem, BidSheet, CompanyInfo, Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "company", "email", "phone", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class BidSheetForm(forms.ModelForm):
    class Meta:
        model = BidSheet
        fields = [
            "title",
            "customer",
            "project_description",
            "project_address",
            "valid_until",
            "discount_percentage",
            "tax_percentage",
            "custom_terms",
            "custom_exclusions",
            "notes",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "project_description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "project_address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "valid_until": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "discount_percentage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "tax_percentage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "custom_terms": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Leave blank to use default terms",
                }
            ),
            "custom_exclusions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Leave blank to use default exclusions",
                }
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class BidItemForm(forms.ModelForm):
    class Meta:
        model = BidItem
        fields = ["service_item", "description", "quantity", "unit_price", "unit_type"]
        widgets = {
            "service_item": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "unit_price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.00"}
            ),
            "unit_type": forms.TextInput(attrs={"class": "form-control"}),
        }


# Create the formset for bid items
BidItemFormSet = inlineformset_factory(
    BidSheet,
    BidItem,
    form=BidItemForm,
    extra=1,
    can_delete=True,
    fields=["service_item", "description", "quantity", "unit_price", "unit_type"],
)


class CompanyInfoForm(forms.ModelForm):
    class Meta:
        model = CompanyInfo
        fields = [
            "name",
            "address",
            "phone",
            "email",
            "website",
            "default_terms",
            "default_exclusions",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "default_terms": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "default_exclusions": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        }


class EmailBidForm(forms.Form):
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        help_text="Email address to send the bid to",
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Email subject line",
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        help_text="Email message body",
    )
    include_pdf = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Include PDF attachment of the bid",
    )
