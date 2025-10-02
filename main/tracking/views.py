import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CardMoveForm,
    InstallationScheduleForm,
    ProjectCardForm,
    QuickCardForm,
    VehicleDropOffForm,
    VehicleForm,
)
from .models import InstallationSchedule, ProjectCard, Vehicle, VehicleDropOff


@login_required
def dashboard(request):
    """Tracking dashboard with overview metrics"""
    context = {
        "total_cards": ProjectCard.objects.count(),
        "active_cards": ProjectCard.objects.exclude(
            status__in=["tech_completed", "print_delivered"]
        ).count(),
        "overdue_cards": ProjectCard.objects.filter(
            sla_breached=True, completed_at__isnull=True
        ).count(),
        "completed_today": ProjectCard.objects.filter(
            completed_at__date=datetime.now().date()
        ).count(),
        "recent_cards": ProjectCard.objects.order_by("-created_at")[:5],
    }
    return render(request, "tracking/dashboard.html", context)


@login_required
def kanban_board(request):
    """Main Kanban board view"""
    # Get cards by status for each department
    tech_cards = ProjectCard.objects.filter(department="technology").order_by(
        "sort_order", "-priority"
    )
    print_cards = ProjectCard.objects.filter(department="print_design").order_by(
        "sort_order", "-priority"
    )

    # Organize cards by status
    tech_columns = {
        "backlog": tech_cards.filter(status="tech_backlog"),
        "in_progress": tech_cards.filter(status="tech_in_progress"),
        "awaiting_client": tech_cards.filter(status="tech_awaiting_client"),
        "testing": tech_cards.filter(status="tech_testing"),
        "completed": tech_cards.filter(status="tech_completed"),
    }

    print_columns = {
        "design_brief": print_cards.filter(status="print_design_brief"),
        "design_phase": print_cards.filter(status="print_design_phase"),
        "client_approval": print_cards.filter(status="print_client_approval"),
        "production": print_cards.filter(status="print_production"),
        "quality_check": print_cards.filter(status="print_quality_check"),
        "delivered": print_cards.filter(status="print_delivered"),
    }

    # SLA alerts
    overdue_cards = ProjectCard.objects.filter(sla_breached=True, completed_at__isnull=True)

    context = {
        "tech_columns": tech_columns,
        "print_columns": print_columns,
        "overdue_cards": overdue_cards,
        "total_cards": ProjectCard.objects.count(),
        "completed_today": ProjectCard.objects.filter(
            completed_at__date=datetime.now().date()
        ).count(),
    }

    return render(request, "tracking/kanban_board.html", context)


@login_required
def kanban_mobile(request):
    """Mobile-optimized Kanban board view"""
    # Simple card organization for mobile
    cards = ProjectCard.objects.all().order_by("-created_at")

    # Organize by simplified status
    backlog_cards = cards.filter(status__in=["tech_backlog", "print_design_brief"])
    in_progress_cards = cards.filter(
        status__in=[
            "tech_in_progress",
            "print_design_phase",
            "tech_testing",
            "print_production",
        ]
    )
    review_cards = cards.filter(
        status__in=[
            "tech_awaiting_client",
            "print_client_approval",
            "print_quality_check",
        ]
    )
    done_cards = cards.filter(status__in=["tech_completed", "print_delivered"])

    context = {
        "backlog_cards": backlog_cards,
        "in_progress_cards": in_progress_cards,
        "review_cards": review_cards,
        "done_cards": done_cards,
        "backlog_count": backlog_cards.count(),
        "in_progress_count": in_progress_cards.count(),
        "review_count": review_cards.count(),
        "done_count": done_cards.count(),
    }

    return render(request, "tracking/kanban_mobile.html", context)


@login_required
def card_list(request):
    """List all project cards"""
    cards = ProjectCard.objects.all().order_by("-created_at")

    # Filter by department
    department = request.GET.get("department")
    if department:
        cards = cards.filter(department=department)

    # Filter by status
    status = request.GET.get("status")
    if status:
        cards = cards.filter(status=status)

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        cards = cards.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(cards, 25)
    page = request.GET.get("page")
    cards = paginator.get_page(page)

    return render(
        request,
        "tracking/card_list.html",
        {
            "cards": cards,
            "search_query": search_query,
            "department_filter": department,
            "status_filter": status,
            "department_choices": ProjectCard.DEPARTMENT_CHOICES,
            "status_choices": ProjectCard.STATUS_CHOICES,
        },
    )


@login_required
def card_create(request):
    """Create new project card"""
    if request.method == "POST":
        form = ProjectCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.created_by = request.user
            card.save()
            messages.success(request, f'Project card "{card.title}" created successfully.')
            return redirect("tracking:card_detail", pk=card.pk)
    else:
        form = ProjectCardForm()

    return render(
        request,
        "tracking/card_form.html",
        {"form": form, "title": "Create Project Card"},
    )


@login_required
def card_detail(request, pk):
    """View project card details"""
    card = get_object_or_404(ProjectCard, pk=pk)
    return render(request, "tracking/card_detail.html", {"card": card})


@login_required
def card_edit(request, pk):
    """Edit project card"""
    card = get_object_or_404(ProjectCard, pk=pk)

    if request.method == "POST":
        form = ProjectCardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project card "{card.title}" updated successfully.')
            return redirect("tracking:card_detail", pk=card.pk)
    else:
        form = ProjectCardForm(instance=card)

    return render(
        request,
        "tracking/card_form.html",
        {"form": form, "card": card, "title": "Edit Project Card"},
    )


@login_required
def card_move(request, pk):
    """Move card to different status (AJAX)"""
    if request.method == "POST":
        card = get_object_or_404(ProjectCard, pk=pk)
        new_status = request.POST.get("status")

        if new_status in dict(ProjectCard.STATUS_CHOICES):
            card.status = new_status
            card.save()
            return JsonResponse({"success": True})

    return JsonResponse({"success": False})


@login_required
@login_required
def vehicle_list(request):
    """List all vehicles with filtering and pagination"""
    from datetime import date

    from django.core.paginator import Paginator

    vehicles = Vehicle.objects.all().order_by("license_plate")

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        vehicles = vehicles.filter(
            Q(license_plate__icontains=search_query)
            | Q(make__icontains=search_query)
            | Q(model__icontains=search_query)
            | Q(vin__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get("status")
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)

    # Type filter
    type_filter = request.GET.get("vehicle_type")
    if type_filter:
        vehicles = vehicles.filter(vehicle_type=type_filter)

    # Calculate summary stats
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status="active").count()
    maintenance_vehicles = Vehicle.objects.filter(status="maintenance").count()
    out_of_service_vehicles = Vehicle.objects.filter(status="out_of_service").count()

    # Pagination
    paginator = Paginator(vehicles, 25)
    page = request.GET.get("page")
    vehicles = paginator.get_page(page)

    return render(
        request,
        "tracking/vehicle_list.html",
        {
            "vehicles": vehicles,
            "search_query": search_query,
            "status_filter": status_filter,
            "type_filter": type_filter,
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "maintenance_vehicles": maintenance_vehicles,
            "out_of_service_vehicles": out_of_service_vehicles,
            "today": date.today(),
        },
    )


@login_required
def vehicle_create(request):
    """Create new vehicle"""
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle added successfully.")
            return redirect("tracking:vehicle_list")
    else:
        form = VehicleForm()

    return render(request, "tracking/vehicle_form.html", {"form": form, "title": "Add Vehicle"})


@login_required
def vehicle_detail(request, pk):
    """View vehicle details"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    recent_dropoffs = vehicle.drop_offs.order_by("-scheduled_drop_off")[:10]

    return render(
        request,
        "tracking/vehicle_detail.html",
        {"vehicle": vehicle, "recent_dropoffs": recent_dropoffs},
    )


@login_required
def vehicle_edit(request, pk):
    """Edit vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated successfully.")
            return redirect("tracking:vehicle_detail", pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)

    return render(
        request,
        "tracking/vehicle_form.html",
        {"form": form, "vehicle": vehicle, "title": "Edit Vehicle"},
    )


@login_required
def dropoff_list(request):
    """List vehicle drop-offs"""
    dropoffs = VehicleDropOff.objects.all().order_by("-scheduled_drop_off")

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        dropoffs = dropoffs.filter(status=status_filter)

    # Pagination
    paginator = Paginator(dropoffs, 25)
    page = request.GET.get("page")
    dropoffs = paginator.get_page(page)

    return render(
        request,
        "tracking/dropoff_list.html",
        {
            "dropoffs": dropoffs,
            "status_filter": status_filter,
            "status_choices": VehicleDropOff.DROP_OFF_STATUS_CHOICES,
        },
    )


@login_required
def dropoff_create(request):
    """Create new vehicle drop-off"""
    if request.method == "POST":
        form = VehicleDropOffForm(request.POST)
        if form.is_valid():
            dropoff = form.save(commit=False)
            dropoff.created_by = request.user
            dropoff.save()
            messages.success(request, "Vehicle drop-off scheduled successfully.")
            return redirect("tracking:dropoff_detail", pk=dropoff.pk)
    else:
        form = VehicleDropOffForm()

    return render(
        request,
        "tracking/dropoff_form.html",
        {"form": form, "title": "Schedule Vehicle Drop-off"},
    )


@login_required
def dropoff_detail(request, pk):
    """View drop-off details"""
    dropoff = get_object_or_404(VehicleDropOff, pk=pk)
    return render(request, "tracking/dropoff_detail.html", {"dropoff": dropoff})


@login_required
def dropoff_edit(request, pk):
    """Edit vehicle drop-off"""
    dropoff = get_object_or_404(VehicleDropOff, pk=pk)

    if request.method == "POST":
        form = VehicleDropOffForm(request.POST, instance=dropoff)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle drop-off updated successfully.")
            return redirect("tracking:dropoff_detail", pk=dropoff.pk)
    else:
        form = VehicleDropOffForm(instance=dropoff)

    return render(
        request,
        "tracking/dropoff_form.html",
        {"form": form, "dropoff": dropoff, "title": "Edit Vehicle Drop-off"},
    )


@login_required
def installation_list(request):
    """List installations"""
    installations = InstallationSchedule.objects.all().order_by("scheduled_date")

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        installations = installations.filter(status=status_filter)

    # Pagination
    paginator = Paginator(installations, 25)
    page = request.GET.get("page")
    installations = paginator.get_page(page)

    return render(
        request,
        "tracking/installation_list.html",
        {
            "installations": installations,
            "status_filter": status_filter,
            "status_choices": InstallationSchedule.INSTALL_STATUS_CHOICES,
        },
    )


@login_required
def installation_create(request):
    """Create new installation"""
    if request.method == "POST":
        form = InstallationScheduleForm(request.POST)
        if form.is_valid():
            installation = form.save(commit=False)
            installation.created_by = request.user
            installation.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, "Installation scheduled successfully.")
            return redirect("tracking:installation_detail", pk=installation.pk)
    else:
        form = InstallationScheduleForm()

    return render(
        request,
        "tracking/installation_form.html",
        {"form": form, "title": "Schedule Installation"},
    )


@login_required
def installation_detail(request, pk):
    """View installation details"""
    installation = get_object_or_404(InstallationSchedule, pk=pk)
    return render(request, "tracking/installation_detail.html", {"installation": installation})


@login_required
def installation_edit(request, pk):
    """Edit installation"""
    installation = get_object_or_404(InstallationSchedule, pk=pk)

    if request.method == "POST":
        form = InstallationScheduleForm(request.POST, instance=installation)
        if form.is_valid():
            form.save()
            messages.success(request, "Installation updated successfully.")
            return redirect("tracking:installation_detail", pk=installation.pk)
    else:
        form = InstallationScheduleForm(instance=installation)

    return render(
        request,
        "tracking/installation_form.html",
        {"form": form, "installation": installation, "title": "Edit Installation"},
    )


@login_required
def sla_report(request):
    """SLA performance report"""
    # Get SLA statistics
    total_cards = ProjectCard.objects.count()
    breached_cards = ProjectCard.objects.filter(sla_breached=True).count()
    active_cards = ProjectCard.objects.filter(completed_at__isnull=True).count()

    # Recent SLA breaches
    recent_breaches = ProjectCard.objects.filter(sla_breached=True).order_by("-created_at")[:10]

    context = {
        "total_cards": total_cards,
        "breached_cards": breached_cards,
        "active_cards": active_cards,
        "breach_rate": (breached_cards / total_cards * 100) if total_cards > 0 else 0,
        "recent_breaches": recent_breaches,
    }

    return render(request, "tracking/sla_report.html", context)


@login_required
def vehicle_report(request):
    """Vehicle usage report"""
    vehicles = Vehicle.objects.annotate(dropoff_count=Count("drop_offs")).order_by(
        "-dropoff_count"
    )

    return render(request, "tracking/vehicle_report.html", {"vehicles": vehicles})


@login_required
def installation_report(request):
    """Installation scheduling report"""
    upcoming_installations = InstallationSchedule.objects.filter(
        scheduled_date__gte=datetime.now()
    ).order_by("scheduled_date")[:20]

    return render(
        request,
        "tracking/installation_report.html",
        {"upcoming_installations": upcoming_installations},
    )
