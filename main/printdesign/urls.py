from django.urls import path

from . import views

app_name = "printdesign"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    path("analytics/", views.dashboard_advanced, name="dashboard_advanced"),
    # Customers
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/create/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_edit, name="customer_edit"),
    # Estimates
    path("estimates/", views.estimate_list, name="estimate_list"),
    path("estimates/create/", views.estimate_create, name="estimate_create"),
    path("estimates/<int:pk>/", views.estimate_detail, name="estimate_detail"),
    path("estimates/<int:pk>/edit/", views.estimate_edit, name="estimate_edit"),
    path("estimates/<int:pk>/pdf/", views.estimate_pdf, name="estimate_pdf"),
    path("estimates/<int:pk>/email/", views.estimate_email, name="estimate_email"),
    path("estimates/<int:pk>/copy/", views.estimate_copy, name="estimate_copy"),
    # Service Items
    path("services/", views.service_list, name="service_list"),
    path("services/create/", views.service_create, name="service_create"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    # Product Sheets
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
]
