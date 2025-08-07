from django import forms
from django.contrib.auth import get_user_model

from .models import Category, CustomerInfo, Priority, Status, Ticket, TicketNote

User = get_user_model()


class TicketForm(forms.ModelForm):
    """Form for creating new tickets"""

    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "customer_name",
            "customer_email",
            "customer_phone",
            "category",
            "priority",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Brief description of the issue",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Detailed description of the issue...",
                }
            ),
            "customer_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Customer name"}
            ),
            "customer_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "customer@email.com"}
            ),
            "customer_phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number (optional)",
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }


class TicketUpdateForm(forms.ModelForm):
    """Form for updating existing tickets"""

    class Meta:
        model = Ticket
        fields = ["title", "description", "status", "priority", "assigned_to"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff users for assignment
        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True)
        self.fields["assigned_to"].empty_label = "Unassigned"


class TicketNoteForm(forms.ModelForm):
    """Form for adding notes to tickets"""

    class Meta:
        model = TicketNote
        fields = ["note", "is_internal"]
        widgets = {
            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Add a note...",
                }
            ),
            "is_internal": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CustomerInfoForm(forms.ModelForm):
    """Form for managing customer information"""

    class Meta:
        model = CustomerInfo
        fields = [
            "customer_name",
            "customer_email",
            "company",
            "phone",
            "computer_make",
            "computer_model",
            "operating_system",
            "os_version",
            "serial_number",
            "notes",
        ]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "customer_email": forms.EmailInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "computer_make": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Dell, HP, Apple"}
            ),
            "computer_model": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Latitude 7420, MacBook Pro",
                }
            ),
            "operating_system": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., Windows 11, macOS Monterey",
                }
            ),
            "os_version": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., 22H2, 12.6"}
            ),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Additional notes about customer setup...",
                }
            ),
        }


class TicketFilterForm(forms.Form):
    """Form for filtering tickets in the dashboard"""

    STATUS_CHOICES = [("", "All Statuses")] + list(Status.choices)
    PRIORITY_CHOICES = [("", "All Priorities")] + list(Priority.choices)
    CATEGORY_CHOICES = [("", "All Categories")] + list(Category.choices)

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        empty_label="All Assignees",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search tickets..."}
        ),
    )
