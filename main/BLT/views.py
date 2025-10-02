from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import TemplateView


# Create your views here.
class Homepage(TemplateView):
    """Homepage view for site"""

    http_method_names = ["get"]
    template_name = "main/home.html"

    def get(self, *args, **kwargs):
        return super().get(self.request)


class HelpdeskView(TemplateView):
    """Helpdesk view for customer support"""

    http_method_names = ["get"]
    template_name = "main/helpdesk.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "support_email": "support@bluelinetech.org",
                "support_phone": "+1 (575) 479-7470",
                "business_hours": "Monday - Friday, 9:00 AM - 5:00 PM MST",
            }
        )
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with department selection"""

    template_name = "main/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = getattr(self.request.user, "profile", None)

        context.update(
            {
                "user_profile": user_profile,
                "can_access_technology": (
                    user_profile.can_access_technology if user_profile else True
                ),
                "can_access_print_design": (
                    user_profile.can_access_print_design if user_profile else False
                ),
                "is_master_user": user_profile.is_master_user if user_profile else False,
            }
        )
        return context


@login_required
def department_redirect(request):
    """Redirect users to appropriate department based on permissions"""
    user_profile = getattr(request.user, "profile", None)

    if user_profile:
        # If user has access to both departments, show dashboard
        if user_profile.is_master_user:
            return redirect("dashboard")
        # If only print design access, go to print dashboard
        elif user_profile.can_access_print_design and not user_profile.can_access_technology:
            return redirect("printdesign:dashboard")
        # If only technology access, go to helpdesk
        elif user_profile.can_access_technology and not user_profile.can_access_print_design:
            return redirect("helpdesk")

    # Default to helpdesk for users without profile
    return redirect("helpdesk")
