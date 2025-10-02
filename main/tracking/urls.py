from django.urls import path

from . import views

app_name = "tracking"

urlpatterns = [
    # Project Cards / Kanban Board
    path("", views.dashboard, name="dashboard"),
    path("kanban/", views.kanban_board, name="kanban_board"),
    path("kanban/mobile/", views.kanban_mobile, name="kanban_mobile"),
    path("cards/", views.card_list, name="card_list"),
    path("cards/create/", views.card_create, name="card_create"),
    path("cards/<int:pk>/", views.card_detail, name="card_detail"),
    path("cards/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path("cards/<int:pk>/move/", views.card_move, name="card_move"),
    # Vehicles
    path("vehicles/", views.vehicle_list, name="vehicle_list"),
    path("vehicles/create/", views.vehicle_create, name="vehicle_create"),
    path("vehicles/<int:pk>/", views.vehicle_detail, name="vehicle_detail"),
    path("vehicles/<int:pk>/edit/", views.vehicle_edit, name="vehicle_edit"),
    # Vehicle Drop-offs
    path("dropoffs/", views.dropoff_list, name="dropoff_list"),
    path("dropoffs/create/", views.dropoff_create, name="dropoff_create"),
    path("dropoffs/<int:pk>/", views.dropoff_detail, name="dropoff_detail"),
    path("dropoffs/<int:pk>/edit/", views.dropoff_edit, name="dropoff_edit"),
    # Installations
    path("installations/", views.installation_list, name="installation_list"),
    path("installations/create/", views.installation_create, name="installation_create"),
    path("installations/<int:pk>/", views.installation_detail, name="installation_detail"),
    path(
        "installations/<int:pk>/edit/",
        views.installation_edit,
        name="installation_edit",
    ),
    # Reports
    path("reports/sla/", views.sla_report, name="sla_report"),
    path("reports/vehicle/", views.vehicle_report, name="vehicle_report"),
    path("reports/installation/", views.installation_report, name="installation_report"),
]
