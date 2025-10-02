from django.urls import path

from . import views

app_name = "bidsheets"

urlpatterns = [
    # Bid Sheet URLs
    path("", views.BidSheetListView.as_view(), name="bid_list"),
    path("create/", views.BidSheetCreateView.as_view(), name="bid_create"),
    path("<int:pk>/", views.BidSheetDetailView.as_view(), name="bid_detail"),
    path("<int:pk>/edit/", views.BidSheetUpdateView.as_view(), name="bid_edit"),
    path("<int:pk>/delete/", views.BidSheetDeleteView.as_view(), name="bid_delete"),
    path("<int:pk>/pdf/", views.generate_bid_pdf, name="bid_pdf"),
    path("<int:pk>/email/", views.email_bid, name="bid_email"),
    # Customer URLs
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path(
        "customers/<int:pk>/edit/",
        views.CustomerUpdateView.as_view(),
        name="customer_edit",
    ),
    # Settings
    path("settings/", views.company_settings, name="company_settings"),
    # AJAX endpoints
    path(
        "api/service-item-details/",
        views.get_service_item_details,
        name="service_item_details",
    ),
]
