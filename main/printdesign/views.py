import io
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

# PDF generation imports
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .forms import (
    EmailEstimateForm,
    PrintCustomerForm,
    PrintEstimateForm,
    PrintServiceItemForm,
    ProductSheetForm,
)
from .models import (
    PrintCustomer,
    PrintEstimate,
    PrintEstimateItem,
    PrintServiceCategory,
    PrintServiceItem,
    ProductSheet,
)


@login_required
def dashboard(request):
    """Print & Design dashboard with advanced analytics"""
    from datetime import date, timedelta

    from django.db.models import Avg, Max, Min

    # Date ranges for analytics
    today = date.today()
    last_30_days = today - timedelta(days=30)
    last_90_days = today - timedelta(days=90)
    current_year = today.year

    # Basic counts
    total_customers = PrintCustomer.objects.count()
    total_estimates = PrintEstimate.objects.count()
    active_estimates = PrintEstimate.objects.filter(
        status__in=["draft", "sent", "approved"]
    ).count()

    # Revenue analytics
    revenue_this_month = (
        PrintEstimate.objects.filter(
            status="approved",
            created_date__month=today.month,
            created_date__year=current_year,
        ).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    revenue_last_30_days = (
        PrintEstimate.objects.filter(status="approved", created_date__gte=last_30_days).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    revenue_this_year = (
        PrintEstimate.objects.filter(status="approved", created_date__year=current_year).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    # Average estimate value
    avg_estimate_value = (
        PrintEstimate.objects.filter(status="approved").aggregate(avg=Avg("total_amount"))["avg"]
        or 0
    )

    # Customer analytics
    new_customers_this_month = PrintCustomer.objects.filter(
        created_at__month=today.month, created_at__year=current_year
    ).count()

    # Top customers by revenue
    top_customers = (
        PrintCustomer.objects.annotate(
            total_revenue=Sum("estimates__total_amount", filter=Q(estimates__status="approved"))
        )
        .exclude(total_revenue__isnull=True)
        .order_by("-total_revenue")[:5]
    )

    # Recent activity
    recent_estimates = PrintEstimate.objects.order_by("-created_date")[:10]
    pending_estimates = PrintEstimate.objects.filter(status="sent").order_by("-created_date")[:5]

    # Status distribution
    status_counts = PrintEstimate.objects.values("status").annotate(count=Count("status"))

    # Monthly revenue trend (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=30 * i)
        revenue = (
            PrintEstimate.objects.filter(
                status="approved",
                created_date__month=month_date.month,
                created_date__year=month_date.year,
            ).aggregate(total=Sum("total_amount"))["total"]
            or 0
        )
        monthly_revenue.append({"month": month_date.strftime("%B %Y"), "revenue": float(revenue)})
    monthly_revenue.reverse()

    context = {
        "total_customers": total_customers,
        "total_estimates": total_estimates,
        "active_estimates": active_estimates,
        "revenue_this_month": revenue_this_month,
        "revenue_last_30_days": revenue_last_30_days,
        "revenue_this_year": revenue_this_year,
        "avg_estimate_value": avg_estimate_value,
        "new_customers_this_month": new_customers_this_month,
        "top_customers": top_customers,
        "recent_estimates": recent_estimates,
        "pending_estimates": pending_estimates,
        "status_counts": status_counts,
        "monthly_revenue": monthly_revenue,
        "pending_approval": PrintEstimate.objects.filter(status="sent").count(),
    }
    return render(request, "printdesign/dashboard.html", context)


@login_required
def dashboard_advanced(request):
    """Advanced analytics dashboard with charts and detailed metrics"""
    from datetime import date, timedelta

    from django.db.models import Avg, Max, Min

    # Date ranges for analytics
    today = date.today()
    last_30_days = today - timedelta(days=30)
    last_90_days = today - timedelta(days=90)
    current_year = today.year

    # Basic counts
    total_customers = PrintCustomer.objects.count()
    total_estimates = PrintEstimate.objects.count()
    active_estimates = PrintEstimate.objects.filter(
        status__in=["draft", "sent", "approved"]
    ).count()

    # Revenue analytics
    revenue_this_month = (
        PrintEstimate.objects.filter(
            status="approved",
            created_date__month=today.month,
            created_date__year=current_year,
        ).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    revenue_last_30_days = (
        PrintEstimate.objects.filter(status="approved", created_date__gte=last_30_days).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    revenue_this_year = (
        PrintEstimate.objects.filter(status="approved", created_date__year=current_year).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    # Average estimate value
    avg_estimate_value = (
        PrintEstimate.objects.filter(status="approved").aggregate(avg=Avg("total_amount"))["avg"]
        or 0
    )

    # Customer analytics
    new_customers_this_month = PrintCustomer.objects.filter(
        created_at__month=today.month, created_at__year=current_year
    ).count()

    # Top customers by revenue
    top_customers = (
        PrintCustomer.objects.annotate(
            total_revenue=Sum("estimates__total_amount", filter=Q(estimates__status="approved"))
        )
        .exclude(total_revenue__isnull=True)
        .order_by("-total_revenue")[:5]
    )

    # Recent activity
    recent_estimates = PrintEstimate.objects.order_by("-created_date")[:10]
    pending_estimates = PrintEstimate.objects.filter(status="sent").order_by("-created_date")[:5]

    # Status distribution
    status_counts = PrintEstimate.objects.values("status").annotate(count=Count("status"))

    # Monthly revenue trend (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=30 * i)
        revenue = (
            PrintEstimate.objects.filter(
                status="approved",
                created_date__month=month_date.month,
                created_date__year=month_date.year,
            ).aggregate(total=Sum("total_amount"))["total"]
            or 0
        )
        monthly_revenue.append({"month": month_date.strftime("%B %Y"), "revenue": float(revenue)})
    monthly_revenue.reverse()

    context = {
        "total_customers": total_customers,
        "total_estimates": total_estimates,
        "active_estimates": active_estimates,
        "revenue_this_month": revenue_this_month,
        "revenue_last_30_days": revenue_last_30_days,
        "revenue_this_year": revenue_this_year,
        "avg_estimate_value": avg_estimate_value,
        "new_customers_this_month": new_customers_this_month,
        "top_customers": top_customers,
        "recent_estimates": recent_estimates,
        "pending_estimates": pending_estimates,
        "status_counts": list(status_counts),
        "monthly_revenue": monthly_revenue,
        "pending_approval": PrintEstimate.objects.filter(status="sent").count(),
    }
    return render(request, "printdesign/dashboard_advanced.html", context)


@login_required
def customer_list(request):
    """List all print customers"""
    customers = PrintCustomer.objects.all().order_by("name")

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(customers, 25)
    page = request.GET.get("page")
    customers = paginator.get_page(page)

    return render(
        request,
        "printdesign/customer_list.html",
        {"customers": customers, "search_query": search_query},
    )


@login_required
def customer_create(request):
    """Create new print customer"""
    if request.method == "POST":
        form = PrintCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            messages.success(request, f'Customer "{customer.name}" created successfully.')
            return redirect("printdesign:customer_detail", pk=customer.pk)
    else:
        form = PrintCustomerForm()

    return render(
        request,
        "printdesign/customer_form.html",
        {"form": form, "title": "Create Customer"},
    )


@login_required
def customer_detail(request, pk):
    """View customer details"""
    customer = get_object_or_404(PrintCustomer, pk=pk)
    recent_estimates = customer.estimates.order_by("-created_date")[:10]

    return render(
        request,
        "printdesign/customer_detail.html",
        {"customer": customer, "recent_estimates": recent_estimates},
    )


@login_required
def customer_edit(request, pk):
    """Edit customer"""
    customer = get_object_or_404(PrintCustomer, pk=pk)

    if request.method == "POST":
        form = PrintCustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer "{customer.name}" updated successfully.')
            return redirect("printdesign:customer_detail", pk=customer.pk)
    else:
        form = PrintCustomerForm(instance=customer)

    return render(
        request,
        "printdesign/customer_form.html",
        {"form": form, "customer": customer, "title": "Edit Customer"},
    )


@login_required
def estimate_list(request):
    """List all estimates"""
    estimates = PrintEstimate.objects.all().order_by("-created_date")

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        estimates = estimates.filter(status=status_filter)

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        estimates = estimates.filter(
            Q(estimate_number__icontains=search_query)
            | Q(customer__name__icontains=search_query)
            | Q(title__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(estimates, 25)
    page = request.GET.get("page")
    estimates = paginator.get_page(page)

    return render(
        request,
        "printdesign/estimate_list.html",
        {
            "estimates": estimates,
            "search_query": search_query,
            "status_filter": status_filter,
            "status_choices": PrintEstimate.STATUS_CHOICES,
        },
    )


@login_required
def estimate_create(request):
    """Create new estimate"""
    if request.method == "POST":
        form = PrintEstimateForm(request.POST)
        if form.is_valid():
            estimate = form.save(commit=False)
            estimate.created_by = request.user
            estimate.save()
            messages.success(
                request, f'Estimate "{estimate.estimate_number}" created successfully.'
            )
            return redirect("printdesign:estimate_detail", pk=estimate.pk)
    else:
        form = PrintEstimateForm()

    return render(
        request,
        "printdesign/estimate_form.html",
        {"form": form, "title": "Create Estimate"},
    )


@login_required
def estimate_detail(request, pk):
    """View estimate details"""
    estimate = get_object_or_404(PrintEstimate, pk=pk)

    return render(request, "printdesign/estimate_detail.html", {"estimate": estimate})


@login_required
def estimate_edit(request, pk):
    """Edit estimate"""
    estimate = get_object_or_404(PrintEstimate, pk=pk)

    if request.method == "POST":
        form = PrintEstimateForm(request.POST, instance=estimate)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Estimate "{estimate.estimate_number}" updated successfully.'
            )
            return redirect("printdesign:estimate_detail", pk=estimate.pk)
    else:
        form = PrintEstimateForm(instance=estimate)

    return render(
        request,
        "printdesign/estimate_form.html",
        {"form": form, "estimate": estimate, "title": "Edit Estimate"},
    )


@login_required
def estimate_pdf(request, pk):
    """Generate PDF for estimate"""
    estimate = get_object_or_404(PrintEstimate, pk=pk)

    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="estimate_{estimate.estimate_number}.pdf"'
    )

    # Create the PDF object
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.blue,
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=12,
    )

    # Company header
    elements.append(Paragraph("<b>Blue Line Print & Design</b>", title_style))
    elements.append(
        Paragraph(
            "814 E. 10th Street<br/>Alamogordo, NM 88310<br/>Phone: 575-479-7470",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 20))

    # Estimate title
    elements.append(Paragraph(f"<b>PRINT ESTIMATE - {estimate.estimate_number}</b>", title_style))
    elements.append(Spacer(1, 12))

    # Customer and project info
    customer_data = [
        ["Customer:", estimate.customer.name],
        ["Company:", estimate.customer.company or "N/A"],
        ["Phone:", estimate.customer.phone or "N/A"],
        ["Email:", estimate.customer.email or "N/A"],
        ["Project:", estimate.project_name or "N/A"],
        ["Date:", estimate.created_date.strftime("%B %d, %Y")],
        [
            "Valid Until:",
            (estimate.valid_until.strftime("%B %d, %Y") if estimate.valid_until else "N/A"),
        ],
    ]

    customer_table = Table(customer_data, colWidths=[1.5 * inch, 4 * inch])
    customer_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # Project description
    if estimate.project_description:
        elements.append(Paragraph("Project Description:", heading_style))
        elements.append(Paragraph(estimate.project_description, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Items table
    items_data = [["Description", "Quantity", "Unit Price", "Setup Fee", "Total"]]

    for item in estimate.items.all():
        items_data.append(
            [
                item.description,
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.setup_fee:.2f}" if item.setup_fee else "$0.00",
                f"${item.total_price:.2f}",
            ]
        )

    # Add totals
    items_data.extend(
        [
            ["", "", "", "Subtotal:", f"${estimate.subtotal:.2f}"],
            [
                "",
                "",
                "",
                f"Discount ({estimate.discount_percentage}%):",
                f"-${estimate.discount_amount:.2f}",
            ],
            [
                "",
                "",
                "",
                f"Tax ({estimate.tax_percentage}%):",
                f"${estimate.tax_amount:.2f}",
            ],
            ["", "", "", "Total:", f"${estimate.total_amount:.2f}"],
        ]
    )

    items_table = Table(items_data, colWidths=[2.5 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch])
    items_table.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                # Data rows
                ("BACKGROUND", (0, 1), (-1, -5), colors.beige),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                # Total rows
                ("FONTNAME", (0, -4), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
            ]
        )
    )

    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Special instructions
    if estimate.special_instructions:
        elements.append(Paragraph("Special Instructions:", heading_style))
        formatted_instructions = estimate.special_instructions.replace("\n", "<br/>")
        elements.append(Paragraph(formatted_instructions, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Terms and conditions
    elements.append(Paragraph("Terms & Conditions:", heading_style))
    terms_text = f"""
    Payment Terms: {estimate.payment_terms}<br/>
    {f'Warranty: {estimate.warranty_terms}<br/>' if estimate.warranty_terms else ''}
    {f'Delivery: {estimate.delivery_terms}<br/>' if estimate.delivery_terms else ''}
    """
    elements.append(Paragraph(terms_text, styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(
        Paragraph("Thank you for choosing Blue Line Print & Design!", styles["Normal"])
    )

    # Build PDF
    doc.build(elements)

    return response


@login_required
def estimate_email(request, pk):
    """Email estimate to customer"""
    estimate = get_object_or_404(PrintEstimate, pk=pk)

    if request.method == "POST":
        form = EmailEstimateForm(request.POST)
        if form.is_valid():
            try:
                # Prepare email details
                recipient_email = form.cleaned_data["recipient_email"]
                subject = form.cleaned_data["subject"]
                message_body = form.cleaned_data["message"]
                include_pdf = form.cleaned_data["include_pdf"]
                copy_to_sender = form.cleaned_data["copy_to_sender"]

                # Create email
                email_recipients = [recipient_email]
                if copy_to_sender:
                    email_recipients.append(request.user.email)

                email = EmailMessage(
                    subject=subject,
                    body=message_body,
                    from_email=None,  # Will use DEFAULT_FROM_EMAIL
                    to=email_recipients,
                )

                # Attach PDF if requested
                if include_pdf:
                    # Generate PDF content
                    pdf_response = estimate_pdf(request, pk)
                    pdf_content = pdf_response.content

                    # Attach PDF to email
                    email.attach(
                        f"estimate_{estimate.estimate_number}.pdf",
                        pdf_content,
                        "application/pdf",
                    )

                # Send email
                email.send()

                # Log success
                messages.success(
                    request,
                    (
                        f"Estimate {estimate.estimate_number} emailed successfully to"
                        f" {recipient_email}"
                    ),
                )
                return redirect("printdesign:estimate_detail", pk=estimate.pk)

            except Exception as e:
                messages.error(request, f"Failed to send email: {str(e)}")
    else:
        # Pre-populate form with customer email and default content
        initial_data = {
            "recipient_email": estimate.customer.email,
            "subject": f"Print Estimate #{estimate.estimate_number} from Blue Line Print & Design",
            "message": f"""Dear {estimate.customer.name},

Please find attached our print estimate #{estimate.estimate_number} for your review.

Project Details:
- Project: {estimate.project_name}
- Total Amount: ${estimate.total_amount:,.2f}
- Valid Until: {estimate.valid_until.strftime('%B %d, %Y') if estimate.valid_until else 'Upon request'}

If you have any questions about this estimate, please don't hesitate to contact us.

Thank you for considering Blue Line Print & Design for your project needs.

Best regards,
Blue Line Print & Design
814 E. 10th Street
Alamogordo, NM 88310
Phone: 575-479-7470
Email: estimates@bluelinetech.org""",
            "include_pdf": True,
        }
        form = EmailEstimateForm(initial=initial_data)

    return render(
        request,
        "printdesign/estimate_email.html",
        {
            "estimate": estimate,
            "form": form,
        },
    )


@login_required
def estimate_copy(request, pk):
    """Copy existing estimate"""
    original = get_object_or_404(PrintEstimate, pk=pk)

    # Create a copy
    estimate = PrintEstimate.objects.get(pk=pk)
    estimate.pk = None
    estimate.estimate_number = None  # Will be auto-generated
    estimate.status = "draft"
    estimate.created_by = request.user
    estimate.created_date = datetime.now().date()
    estimate.save()

    # Copy estimate items
    for item in original.items.all():
        item.pk = None
        item.estimate = estimate
        item.save()

    messages.success(
        request,
        f"Estimate copied successfully. New estimate: {estimate.estimate_number}",
    )
    return redirect("printdesign:estimate_detail", pk=estimate.pk)


@login_required
def service_list(request):
    """List all service items"""
    services = PrintServiceItem.objects.all().order_by("category__name", "name")

    return render(request, "printdesign/service_list.html", {"services": services})


@login_required
def service_create(request):
    """Create new service item"""
    if request.method == "POST":
        form = PrintServiceItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service item created successfully.")
            return redirect("printdesign:service_list")
    else:
        form = PrintServiceItemForm()

    return render(
        request,
        "printdesign/service_form.html",
        {"form": form, "title": "Create Service Item"},
    )


@login_required
def service_edit(request, pk):
    """Edit service item"""
    service = get_object_or_404(PrintServiceItem, pk=pk)

    if request.method == "POST":
        form = PrintServiceItemForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service item updated successfully.")
            return redirect("printdesign:service_list")
    else:
        form = PrintServiceItemForm(instance=service)

    return render(
        request,
        "printdesign/service_form.html",
        {"form": form, "service": service, "title": "Edit Service Item"},
    )


@login_required
def product_list(request):
    """List all product sheets"""
    products = ProductSheet.objects.all().order_by("product_type", "name")

    return render(request, "printdesign/product_list.html", {"products": products})


@login_required
def product_create(request):
    """Create new product sheet"""
    if request.method == "POST":
        form = ProductSheetForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            messages.success(request, f'Product "{product.name}" created successfully.')
            return redirect("printdesign:product_detail", pk=product.pk)
    else:
        form = ProductSheetForm()

    return render(
        request,
        "printdesign/product_form.html",
        {"form": form, "title": "Create Product"},
    )


@login_required
def product_detail(request, pk):
    """View product details"""
    product = get_object_or_404(ProductSheet, pk=pk)

    return render(request, "printdesign/product_detail.html", {"product": product})


@login_required
def product_edit(request, pk):
    """Edit product sheet"""
    product = get_object_or_404(ProductSheet, pk=pk)

    if request.method == "POST":
        form = ProductSheetForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully.')
            return redirect("printdesign:product_detail", pk=product.pk)
    else:
        form = ProductSheetForm(instance=product)

    return render(
        request,
        "printdesign/product_form.html",
        {"form": form, "product": product, "title": "Edit Product"},
    )


@login_required
def product_edit(request, pk):
    """Edit existing product"""
    product = get_object_or_404(ProductSheet, pk=pk)

    if request.method == "POST":
        form = ProductSheetForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully.')
            return redirect("printdesign:product_detail", pk=product.pk)
    else:
        form = ProductSheetForm(instance=product)

    return render(
        request,
        "printdesign/product_form.html",
        {"form": form, "product": product, "title": "Edit Product"},
    )
