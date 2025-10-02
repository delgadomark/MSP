from datetime import datetime, timedelta

from django import forms
from django.contrib.auth.models import User
from printdesign.models import PrintCustomer, PrintEstimate

from .models import InstallationSchedule, ProjectCard, Vehicle, VehicleDropOff


class ProjectCardForm(forms.ModelForm):
    """Form for creating and editing project cards"""

    class Meta:
        model = ProjectCard
        fields = [
            "title",
            "description",
            "department",
            "status",
            "priority",
            "assigned_to",
            "print_customer",
            "print_estimate",
            "sla_hours",
            "estimated_hours",
            "actual_hours",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Card title"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Detailed description...",
                }
            ),
            "department": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "print_customer": forms.Select(attrs={"class": "form-select"}),
            "print_estimate": forms.Select(attrs={"class": "form-select"}),
            "sla_hours": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "placeholder": "Hours"}
            ),
            "estimated_hours": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.25"}
            ),
            "actual_hours": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.25"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = True
        self.fields["description"].required = True
        self.fields["department"].required = True

        # Filter users to only those with appropriate access
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True)

        # Filter estimates to active ones
        self.fields["print_estimate"].queryset = PrintEstimate.objects.filter(
            status__in=["draft", "sent", "approved"]
        ).order_by("-created_date")

        # Make print fields optional for technology cards
        self.fields["print_customer"].required = False
        self.fields["print_estimate"].required = False

        # Add empty choices
        self.fields["print_customer"].empty_label = "Select customer (optional)"
        self.fields["print_estimate"].empty_label = "Select estimate (optional)"
        self.fields["assigned_to"].empty_label = "Assign to user"

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        print_customer = cleaned_data.get("print_customer")
        print_estimate = cleaned_data.get("print_estimate")

        # Validate print-specific fields for print department
        if department == "print_design":
            if not print_customer:
                raise forms.ValidationError(
                    "Print customer is required for print & design projects."
                )

        return cleaned_data


class VehicleForm(forms.ModelForm):
    """Form for managing vehicles"""

    class Meta:
        model = Vehicle
        fields = [
            "license_plate",
            "make",
            "model",
            "year",
            "color",
            "vin",
            "print_customer",
            "notes",
        ]
        widgets = {
            "license_plate": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "NM-123ABC"}
            ),
            "make": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Vehicle make"}
            ),
            "model": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Vehicle model"}
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1900",
                    "max": datetime.now().year + 2,
                }
            ),
            "color": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Vehicle color"}
            ),
            "vin": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "17-character VIN"}
            ),
            "print_customer": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["license_plate"].required = True
        self.fields["make"].required = True
        self.fields["model"].required = True
        self.fields["year"].required = True

        # Add empty choice for customer
        self.fields["print_customer"].empty_label = "Select customer (optional)"

    def clean_vin(self):
        vin = self.cleaned_data.get("vin")
        if vin and len(vin) != 17:
            raise forms.ValidationError("VIN must be exactly 17 characters.")
        return vin


class VehicleDropOffForm(forms.ModelForm):
    """Form for vehicle drop-offs"""

    class Meta:
        model = VehicleDropOff
        fields = [
            "vehicle",
            "project_card",
            "scheduled_drop_off",
            "expected_completion",
            "work_description",
            "customer_notes",
            "drop_off_contact",
            "status",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select"}),
            "project_card": forms.Select(attrs={"class": "form-select"}),
            "scheduled_drop_off": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "expected_completion": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "work_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Description of work to be performed...",
                }
            ),
            "customer_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Customer notes...",
                }
            ),
            "drop_off_contact": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Contact person"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicle"].required = True
        self.fields["project_card"].required = True
        self.fields["work_description"].required = True

        # Filter to active vehicles only
        self.fields["vehicle"].queryset = Vehicle.objects.all()

        # Filter to active project cards
        self.fields["project_card"].queryset = ProjectCard.objects.filter(
            completed_at__isnull=True
        ).order_by("-created_at")


class InstallationScheduleForm(forms.ModelForm):
    """Form for scheduling installations"""

    class Meta:
        model = InstallationSchedule
        fields = [
            "project_card",
            "install_type",
            "status",
            "scheduled_date",
            "estimated_duration",
            "install_address",
            "special_instructions",
            "equipment_needed",
            "primary_contact",
            "contact_phone",
            "technician_team",
        ]
        widgets = {
            "project_card": forms.Select(attrs={"class": "form-select"}),
            "install_type": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "scheduled_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "estimated_duration": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "install_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Installation address...",
                }
            ),
            "special_instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Special installation instructions...",
                }
            ),
            "equipment_needed": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Required equipment and tools...",
                }
            ),
            "primary_contact": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Contact person name"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "(575) 555-0123"}
            ),
            "technician_team": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project_card"].required = True
        self.fields["scheduled_date"].required = True
        self.fields["install_address"].required = True
        self.fields["primary_contact"].required = True
        self.fields["contact_phone"].required = True

        # Filter to active project cards only
        self.fields["project_card"].queryset = ProjectCard.objects.filter(
            completed_at__isnull=True
        ).order_by("-created_at")

        # Filter to active users for technician team
        self.fields["technician_team"].queryset = User.objects.filter(is_active=True)


class CardMoveForm(forms.Form):
    """Form for moving cards between statuses"""

    new_status = forms.CharField(widget=forms.HiddenInput())
    sort_order = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Optional notes about this status change...",
            }
        ),
    )


class QuickCardForm(forms.Form):
    """Quick card creation form for dashboard"""

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Card title"}),
    )
    department = forms.ChoiceField(
        choices=ProjectCard.DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    priority = forms.ChoiceField(
        choices=ProjectCard.PRIORITY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="Assign to...",
    )
    sla_hours = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "SLA hours"}),
    )


class ProjectCardFilterForm(forms.Form):
    """Form for filtering project cards"""

    department = forms.ChoiceField(
        required=False,
        choices=[("", "All Departments")] + ProjectCard.DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + ProjectCard.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[("", "All Priorities")] + ProjectCard.PRIORITY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="All Users",
    )
    overdue_only = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
