import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import (
    BidItemFormSet,
    BidSheetForm,
    CompanyInfoForm,
    CustomerForm,
    EmailBidForm,
)
from .models import BidEmailLog, BidItem, BidSheet, CompanyInfo, Customer, ServiceItem


class BidSheetListView(LoginRequiredMixin, ListView):
    model = BidSheet
    template_name = "bidsheets/bid_list.html"
    context_object_name = "bids"
    paginate_by = 20

    def get_queryset(self):
        return BidSheet.objects.select_related("customer").order_by("-created_at")


class BidSheetDetailView(LoginRequiredMixin, DetailView):
    model = BidSheet
    template_name = "bidsheets/bid_detail.html"
    context_object_name = "bid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_info"] = CompanyInfo.objects.first()
        return context


class BidSheetCreateView(LoginRequiredMixin, CreateView):
    model = BidSheet
    form_class = BidSheetForm
    template_name = "bidsheets/bid_form.html"

    def get_initial(self):
        """Pre-populate form with customer data if customer_id is provided"""
        initial = super().get_initial()

        # Check for customer_id in URL parameters
        customer_id = self.request.GET.get("customer")
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                initial["customer"] = customer

                # Auto-populate project address with customer address if available
                if customer.address:
                    initial["project_address"] = customer.address

                # Set a default title based on customer
                if customer.company:
                    initial["title"] = f"Service Quote for {customer.company}"
                else:
                    initial["title"] = f"Service Quote for {customer.name}"

            except Customer.DoesNotExist:
                pass

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = BidItemFormSet(self.request.POST)
        else:
            context["formset"] = BidItemFormSet()
        context["service_items"] = ServiceItem.objects.filter(is_active=True).select_related(
            "category"
        )

        # Add customer info to context for JavaScript auto-population
        customer_id = self.request.GET.get("customer")
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                context["selected_customer"] = customer
            except Customer.DoesNotExist:
                pass

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        with transaction.atomic():
            form.instance.created_by = self.request.user
            if not form.instance.valid_until:
                form.instance.valid_until = date.today() + timedelta(days=30)

            self.object = form.save()

            if formset.is_valid():
                formset.instance = self.object
                formset.save()
                self.object.recalculate_totals()

        messages.success(self.request, f"Bid {self.object.bid_number} created successfully!")
        return redirect("bid_detail", pk=self.object.pk)

    def form_invalid(self, form):
        context = self.get_context_data()
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(context)


class BidSheetUpdateView(LoginRequiredMixin, UpdateView):
    model = BidSheet
    form_class = BidSheetForm
    template_name = "bidsheets/bid_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = BidItemFormSet(self.request.POST, instance=self.object)
        else:
            context["formset"] = BidItemFormSet(instance=self.object)
        context["service_items"] = ServiceItem.objects.filter(is_active=True).select_related(
            "category"
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        with transaction.atomic():
            self.object = form.save()

            if formset.is_valid():
                formset.save()
                self.object.recalculate_totals()

        messages.success(self.request, f"Bid {self.object.bid_number} updated successfully!")
        return redirect("bid_detail", pk=self.object.pk)

    def form_invalid(self, form):
        context = self.get_context_data()
        messages.error(self.request, "Please correct the errors below.")
        return self.render_to_response(context)


class BidSheetDeleteView(LoginRequiredMixin, DeleteView):
    model = BidSheet
    template_name = "bidsheets/bid_confirm_delete.html"
    success_url = reverse_lazy("bid_list")

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(request, "Bid deleted successfully!")
        return result


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "bidsheets/customer_list.html"
    context_object_name = "customers"
    paginate_by = 20


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "bidsheets/customer_form.html"
    success_url = reverse_lazy("customer_list")

    def form_valid(self, form):
        messages.success(self.request, f"Customer {form.instance.name} created successfully!")
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "bidsheets/customer_form.html"
    success_url = reverse_lazy("customer_list")

    def form_valid(self, form):
        messages.success(self.request, f"Customer {form.instance.name} updated successfully!")
        return super().form_valid(form)


@login_required
def generate_bid_pdf(request, pk):
    """Generate PDF version of bid sheet"""
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    bid = get_object_or_404(BidSheet, pk=pk)

    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="bid_{bid.bid_number}.pdf"'

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

    # Company info
    company_info = CompanyInfo.objects.first()
    if company_info:
        # Company header
        elements.append(Paragraph(f"<b>{company_info.name}</b>", title_style))
        elements.append(Paragraph(company_info.address.replace("\n", "<br/>"), styles["Normal"]))
        elements.append(Paragraph(f"Phone: {company_info.phone}", styles["Normal"]))
        if company_info.email:
            elements.append(Paragraph(f"Email: {company_info.email}", styles["Normal"]))
        elements.append(Spacer(1, 20))

    # Bid title
    elements.append(Paragraph(f"<b>BID SHEET - {bid.bid_number}</b>", title_style))
    elements.append(Spacer(1, 12))

    # Customer and project info
    customer_data = [
        ["Customer:", bid.customer.name],
        ["Company:", bid.customer.company or "N/A"],
        ["Phone:", bid.customer.phone or "N/A"],
        ["Email:", bid.customer.email or "N/A"],
        ["Project:", bid.title],
        ["Date:", bid.created_at.strftime("%B %d, %Y")],
        [
            "Valid Until:",
            bid.valid_until.strftime("%B %d, %Y") if bid.valid_until else "N/A",
        ],
    ]

    customer_table = Table(customer_data, colWidths=[1.5 * inch, 4 * inch])
    customer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # Project description
    if bid.project_description:
        elements.append(Paragraph("Project Description:", heading_style))
        elements.append(Paragraph(bid.project_description, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Items table
    elements.append(Paragraph("Bid Items:", heading_style))

    # Table headers
    items_data = [["Service", "Description", "Quantity", "Unit Price", "Total"]]

    # Add bid items
    for item in bid.items.all():
        # Get category name safely
        category_name = "Custom"
        if item.service_item and item.service_item.category:
            category_name = item.service_item.category.name
        elif item.service_item:
            category_name = "Service"

        items_data.append(
            [
                category_name,
                item.description[:50] + ("..." if len(item.description) > 50 else ""),
                str(item.quantity),
                f"${item.unit_price:,.2f}",
                f"${item.total_price:,.2f}",
            ]
        )

    # Add subtotal, tax, and total
    items_data.extend(
        [
            ["", "", "", "Subtotal:", f"${bid.subtotal:,.2f}"],
            ["", "", "", f"Tax ({bid.tax_percentage}%):", f"${bid.tax_amount:,.2f}"],
            ["", "", "", "Total:", f"${bid.total_amount:,.2f}"],
        ]
    )

    items_table = Table(
        items_data, colWidths=[1.2 * inch, 2.5 * inch, 0.8 * inch, 1 * inch, 1 * inch]
    )
    items_table.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                # Data rows
                ("BACKGROUND", (0, 1), (-1, -4), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),  # Right align numbers
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                # Total rows
                ("BACKGROUND", (0, -3), (-1, -1), colors.lightgrey),
                ("FONTNAME", (3, -3), (-1, -1), "Helvetica-Bold"),
                ("FONTNAME", (4, -1), (4, -1), "Helvetica-Bold"),
                ("FONTSIZE", (4, -1), (4, -1), 12),
                # Borders
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(items_table)
    elements.append(Spacer(1, 20))

    # Terms and Conditions
    terms_text = (
        bid.custom_terms
        if bid.custom_terms
        else (company_info.default_terms if company_info else "")
    )
    if terms_text:
        elements.append(Paragraph("Terms and Conditions:", heading_style))
        # Replace line breaks with HTML breaks for proper PDF formatting
        formatted_terms = terms_text.replace("\n", "<br/>")
        elements.append(Paragraph(formatted_terms, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Exclusions
    exclusions_text = (
        bid.custom_exclusions
        if bid.custom_exclusions
        else (company_info.default_exclusions if company_info else "")
    )
    if exclusions_text:
        elements.append(Paragraph("Exclusions:", heading_style))
        # Replace line breaks with HTML breaks for proper PDF formatting
        formatted_exclusions = exclusions_text.replace("\n", "<br/>")
        elements.append(Paragraph(formatted_exclusions, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Additional notes
    if bid.notes:
        elements.append(Paragraph("Additional Notes:", heading_style))
        formatted_notes = bid.notes.replace("\n", "<br/>")
        elements.append(Paragraph(formatted_notes, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Thank you for your business!", styles["Normal"]))

    # Build PDF
    doc.build(elements)

    return response


@login_required
def email_bid(request, pk):
    """Email bid sheet to customer"""
    bid = get_object_or_404(BidSheet, pk=pk)

    if request.method == "POST":
        form = EmailBidForm(request.POST)
        if form.is_valid():
            try:
                # Prepare email details
                recipient_email = form.cleaned_data["recipient_email"]
                subject = form.cleaned_data["subject"]
                message_body = form.cleaned_data["message"]
                include_pdf = form.cleaned_data["include_pdf"]

                # Create email
                email = EmailMessage(
                    subject=subject,
                    body=message_body,
                    from_email=None,  # Will use DEFAULT_FROM_EMAIL (bids@bluelinetech.org)
                    to=[recipient_email],
                )

                # Attach PDF if requested
                if include_pdf:
                    # Generate PDF
                    response = generate_bid_pdf(request, pk)
                    pdf_content = response.content

                    # Attach PDF to email
                    email.attach(f"bid_{bid.bid_number}.pdf", pdf_content, "application/pdf")

                # Send email
                email.send()

                # Log the email
                BidEmailLog.objects.create(
                    bid=bid,
                    recipient_email=recipient_email,
                    subject=subject,
                    sent_by=request.user,
                    sent_at=timezone.now(),
                    success=True,
                )

                messages.success(
                    request,
                    f"Bid {bid.bid_number} successfully emailed to {recipient_email}",
                )
                return redirect("bid_detail", pk=pk)

            except Exception as e:
                # Log failed email attempt
                BidEmailLog.objects.create(
                    bid=bid,
                    recipient_email=form.cleaned_data["recipient_email"],
                    subject=form.cleaned_data["subject"],
                    sent_by=request.user,
                    sent_at=timezone.now(),
                    success=False,
                    error_message=str(e),
                )

                messages.error(request, f"Failed to send email: {str(e)}")
    else:
        # Pre-populate form with bid and customer details
        initial_data = {
            "recipient_email": bid.customer.email if bid.customer.email else "",
            "subject": f"Service Quote #{bid.bid_number} from Blue Line Technology",
            "message": f"""Dear {bid.customer.name},

Please find attached our service quote #{bid.bid_number} for your review.

Quote Details:
- Project: {bid.title}
- Total Amount: ${bid.total_amount:,.2f}
- Valid Until: {bid.valid_until.strftime('%B %d, %Y')}

If you have any questions about this quote, please don't hesitate to contact us.

Thank you for considering Blue Line Technology for your project needs.

Best regards,
Blue Line Technology
814 E. 10th Street
Alamogordo, NM 88310
Phone: 575-479-7470
Email: bids@bluelinetech.org""",
            "include_pdf": True,
        }
        form = EmailBidForm(initial=initial_data)

    context = {
        "bid": bid,
        "form": form,
    }
    return render(request, "bidsheets/email_bid.html", context)


@login_required
def company_settings(request):
    """Manage company information"""
    company_info, created = CompanyInfo.objects.get_or_create(
        defaults={
            "name": "Blue Line Technology",
            "address": "814 E. 10th Street\nAlamogordo, NM 88310",
            "phone": "575-479-7470",
        }
    )

    if request.method == "POST":
        form = CompanyInfoForm(request.POST, request.FILES, instance=company_info)
        if form.is_valid():
            form.save()
            messages.success(request, "Company information updated successfully!")
            return redirect("company_settings")
    else:
        form = CompanyInfoForm(instance=company_info)

    return render(
        request,
        "bidsheets/company_settings.html",
        {"form": form, "company_info": company_info},
    )


@csrf_exempt
@login_required
def get_service_item_details(request):
    """AJAX endpoint to get service item details"""
    if request.method == "POST":
        data = json.loads(request.body)
        service_item_id = data.get("service_item_id")

        if service_item_id:
            try:
                item = ServiceItem.objects.get(id=service_item_id)
                return JsonResponse(
                    {
                        "success": True,
                        "name": item.name,
                        "description": item.description,
                        "unit_price": str(item.default_unit_price),
                        "unit_type": item.unit_type,
                    }
                )
            except ServiceItem.DoesNotExist:
                pass

    return JsonResponse({"success": False})
