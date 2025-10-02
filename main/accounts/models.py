from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with department access permissions"""

    DEPARTMENT_CHOICES = [
        ("technology", "Technology"),
        ("print_design", "Print & Design"),
        ("master", "Master Access"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    can_access_technology = models.BooleanField(
        default=False, help_text="Access to technology/IT services"
    )
    can_access_print_design = models.BooleanField(
        default=False, help_text="Access to print and design services"
    )
    primary_department = models.CharField(
        max_length=20, choices=DEPARTMENT_CHOICES, default="technology"
    )
    phone = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_access_level()}"

    @property
    def is_master_user(self):
        """Check if user has access to both departments"""
        return self.can_access_technology and self.can_access_print_design

    def get_access_level(self):
        """Get user's access level description"""
        if self.is_master_user:
            return "Master Access"
        elif self.can_access_technology and self.can_access_print_design:
            return "Both Departments"
        elif self.can_access_technology:
            return "Technology Only"
        elif self.can_access_print_design:
            return "Print & Design Only"
        else:
            return "No Access"

    def get_accessible_departments(self):
        """Get list of departments user can access"""
        departments = []
        if self.can_access_technology:
            departments.append("technology")
        if self.can_access_print_design:
            departments.append("print_design")
        return departments


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Automatically create/update user profile when user is created/updated"""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()
        else:
            UserProfile.objects.create(user=instance)
