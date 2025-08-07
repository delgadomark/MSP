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
