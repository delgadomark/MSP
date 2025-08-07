from django.urls import path

from . import views

app_name = "helpdesk"

urlpatterns = [
    # Dashboard and main views
    path("", views.TicketDashboardView.as_view(), name="dashboard"),
    path("sla-report/", views.sla_report, name="sla_report"),
    # Ticket management
    path("tickets/create/", views.TicketCreateView.as_view(), name="ticket_create"),
    path(
        "tickets/<str:ticket_number>/",
        views.TicketDetailView.as_view(),
        name="ticket_detail",
    ),
    path(
        "tickets/<str:ticket_number>/update/",
        views.TicketUpdateView.as_view(),
        name="ticket_update",
    ),
    path(
        "tickets/<str:ticket_number>/add-note/",
        views.add_ticket_note,
        name="add_ticket_note",
    ),
    # Customer management
    path("customers/", views.CustomerInfoListView.as_view(), name="customer_list"),
    path(
        "customers/create/",
        views.CustomerInfoCreateView.as_view(),
        name="customer_create",
    ),
    path(
        "customers/<int:pk>/",
        views.CustomerInfoDetailView.as_view(),
        name="customer_detail",
    ),
    path(
        "customers/<int:pk>/update/",
        views.CustomerInfoUpdateView.as_view(),
        name="customer_update",
    ),
]
