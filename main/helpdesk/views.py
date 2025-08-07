from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import (
    CustomerInfoForm,
    TicketFilterForm,
    TicketForm,
    TicketNoteForm,
    TicketUpdateForm,
)
from .models import CustomerInfo, SLALevel, Status, Ticket


class TicketDashboardView(LoginRequiredMixin, ListView):  # pylint: disable=too-many-ancestors
    """Main dashboard showing ticket statistics and overview"""

    model = Ticket
    template_name = "helpdesk/dashboard.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        queryset = Ticket.objects.all()
        form = TicketFilterForm(self.request.GET)

        if form.is_valid():
            if form.cleaned_data["status"]:
                queryset = queryset.filter(status=form.cleaned_data["status"])
            if form.cleaned_data["priority"]:
                queryset = queryset.filter(priority=form.cleaned_data["priority"])
            if form.cleaned_data["category"]:
                queryset = queryset.filter(category=form.cleaned_data["category"])
            if form.cleaned_data["assigned_to"]:
                queryset = queryset.filter(assigned_to=form.cleaned_data["assigned_to"])
            if form.cleaned_data["search"]:
                search_term = form.cleaned_data["search"]
                queryset = queryset.filter(
                    Q(ticket_number__icontains=search_term)
                    | Q(title__icontains=search_term)
                    | Q(customer_name__icontains=search_term)
                    | Q(customer_email__icontains=search_term)
                )

        return queryset.select_related("assigned_to")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ticket statistics
        total_tickets = Ticket.objects.count()
        open_tickets = Ticket.objects.exclude(status__in=[Status.RESOLVED, Status.CLOSED]).count()
        overdue_response = Ticket.objects.filter(
            first_response_at__isnull=True, response_due__lt=timezone.now()
        ).count()
        overdue_resolution = (
            Ticket.objects.filter(resolved_at__isnull=True, resolution_due__lt=timezone.now())
            .exclude(status__in=[Status.RESOLVED, Status.CLOSED])
            .count()
        )

        # Priority breakdown
        priority_stats = (
            Ticket.objects.exclude(status__in=[Status.RESOLVED, Status.CLOSED])
            .values("priority")
            .annotate(count=Count("id"))
        )

        # Status breakdown
        status_stats = Ticket.objects.values("status").annotate(count=Count("id"))

        # Recent tickets
        recent_tickets = Ticket.objects.all()[:5]

        context.update(
            {
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "overdue_response": overdue_response,
                "overdue_resolution": overdue_resolution,
                "priority_stats": {item["priority"]: item["count"] for item in priority_stats},
                "status_stats": {item["status"]: item["count"] for item in status_stats},
                "recent_tickets": recent_tickets,
                "filter_form": TicketFilterForm(self.request.GET),
            }
        )

        return context


class TicketDetailView(LoginRequiredMixin, DetailView):  # pylint: disable=too-many-ancestors
    """Detailed view of a single ticket"""

    model = Ticket
    template_name = "helpdesk/ticket_detail.html"
    context_object_name = "ticket"
    slug_field = "ticket_number"
    slug_url_kwarg = "ticket_number"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notes"] = self.object.notes.all()
        context["note_form"] = TicketNoteForm()
        context["update_form"] = TicketUpdateForm(instance=self.object)

        # Get customer info if exists
        try:
            customer_info = CustomerInfo.objects.get(customer_email=self.object.customer_email)
            context["customer_info"] = customer_info
        except CustomerInfo.DoesNotExist:
            context["customer_info"] = None

        return context


class TicketCreateView(LoginRequiredMixin, CreateView):  # pylint: disable=too-many-ancestors
    """Create a new ticket"""

    model = Ticket
    form_class = TicketForm
    template_name = "helpdesk/ticket_create.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Ticket {self.object.ticket_number} created successfully!")
        return response

    def get_success_url(self):
        return reverse_lazy(
            "helpdesk:ticket_detail",
            kwargs={"ticket_number": self.object.ticket_number},
        )


class TicketUpdateView(LoginRequiredMixin, UpdateView):  # pylint: disable=too-many-ancestors
    """Update an existing ticket"""

    model = Ticket
    form_class = TicketUpdateForm
    template_name = "helpdesk/ticket_update.html"
    slug_field = "ticket_number"
    slug_url_kwarg = "ticket_number"

    def form_valid(self, form):
        # Track status changes
        if "status" in form.changed_data:
            new_status = form.cleaned_data["status"]

            # Update timestamps based on status changes
            if new_status == Status.RESOLVED and not self.object.resolved_at:
                form.instance.resolved_at = timezone.now()
            elif new_status == Status.CLOSED and not self.object.closed_at:
                form.instance.closed_at = timezone.now()

        response = super().form_valid(form)
        messages.success(self.request, f"Ticket {self.object.ticket_number} updated successfully!")
        return response

    def get_success_url(self):
        return reverse_lazy(
            "helpdesk:ticket_detail",
            kwargs={"ticket_number": self.object.ticket_number},
        )


@login_required
def add_ticket_note(request, ticket_number):
    """Add a note to a ticket"""
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)

    if request.method == "POST":
        form = TicketNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.ticket = ticket
            note.author = request.user
            note.save()

            # Mark first response if this is the first note
            if not ticket.first_response_at and request.user.is_staff:
                ticket.first_response_at = timezone.now()
                ticket.save()

            messages.success(request, "Note added successfully!")
        else:
            messages.error(request, "Error adding note. Please check your input.")

    return redirect("helpdesk:ticket_detail", ticket_number=ticket_number)


class CustomerInfoListView(LoginRequiredMixin, ListView):  # pylint: disable=too-many-ancestors
    """List all customer information"""

    model = CustomerInfo
    template_name = "helpdesk/customer_list.html"
    context_object_name = "customers"
    paginate_by = 20

    def get_queryset(self):
        queryset = CustomerInfo.objects.all()
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(customer_name__icontains=search)
                | Q(customer_email__icontains=search)
                | Q(company__icontains=search)
                | Q(computer_make__icontains=search)
                | Q(computer_model__icontains=search)
            )
        return queryset


class CustomerInfoDetailView(LoginRequiredMixin, DetailView):  # pylint: disable=too-many-ancestors
    """Detailed view of customer information"""

    model = CustomerInfo
    template_name = "helpdesk/customer_detail.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get tickets for this customer
        context["tickets"] = Ticket.objects.filter(
            customer_email=self.object.customer_email
        ).order_by("-created_at")[:10]
        return context


class CustomerInfoCreateView(LoginRequiredMixin, CreateView):  # pylint: disable=too-many-ancestors
    """Create customer information"""

    model = CustomerInfo
    form_class = CustomerInfoForm
    template_name = "helpdesk/customer_create.html"
    success_url = reverse_lazy("helpdesk:customer_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Customer information created successfully!")
        return response


class CustomerInfoUpdateView(LoginRequiredMixin, UpdateView):  # pylint: disable=too-many-ancestors
    """Update customer information"""

    model = CustomerInfo
    form_class = CustomerInfoForm
    template_name = "helpdesk/customer_update.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Customer information updated successfully!")
        return response

    def get_success_url(self):
        return reverse_lazy("helpdesk:customer_detail", kwargs={"pk": self.object.pk})


@login_required
def sla_report(request):
    """SLA performance report"""
    # Calculate SLA metrics
    total_tickets = Ticket.objects.count()

    # Response SLA metrics
    tickets_with_response = Ticket.objects.filter(first_response_at__isnull=False)
    response_on_time = tickets_with_response.filter(
        first_response_at__lte=timezone.F("response_due")
    ).count()
    response_sla_percentage = (
        (response_on_time / tickets_with_response.count() * 100)
        if tickets_with_response.count() > 0
        else 0
    )

    # Resolution SLA metrics
    resolved_tickets = Ticket.objects.filter(resolved_at__isnull=False)
    resolution_on_time = resolved_tickets.filter(
        resolved_at__lte=timezone.F("resolution_due")
    ).count()
    resolution_sla_percentage = (
        (resolution_on_time / resolved_tickets.count() * 100)
        if resolved_tickets.count() > 0
        else 0
    )

    # Currently overdue tickets
    overdue_response = Ticket.objects.filter(
        first_response_at__isnull=True, response_due__lt=timezone.now()
    )
    overdue_resolution = Ticket.objects.filter(
        resolved_at__isnull=True, resolution_due__lt=timezone.now()
    ).exclude(status__in=[Status.RESOLVED, Status.CLOSED])

    context = {
        "total_tickets": total_tickets,
        "response_sla_percentage": round(response_sla_percentage, 1),
        "resolution_sla_percentage": round(resolution_sla_percentage, 1),
        "overdue_response": overdue_response,
        "overdue_resolution": overdue_resolution,
        "sla_levels": SLALevel.objects.all(),
    }

    return render(request, "helpdesk/sla_report.html", context)
