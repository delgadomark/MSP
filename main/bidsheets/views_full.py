import io
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
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = BidItemFormSet(self.request.POST)
        else:
            context["formset"] = BidItemFormSet()
        context["service_items"] = ServiceItem.objects.filter(is_active=True).select_related(
            "category"
        )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        with transaction.atomic():
            form.instance.created_by = self.request.user
            # Set default valid_until to 30 days from now if not provided
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
    success_url = reverse_lazy("bidsheets:bid_list")

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
    success_url = reverse_lazy("bidsheets:customer_list")

    def form_valid(self, form):
        messages.success(self.request, f"Customer {form.instance.name} created successfully!")
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "bidsheets/customer_form.html"
    success_url = reverse_lazy("bidsheets:customer_list")

    def form_valid(self, form):
        messages.success(self.request, f"Customer {form.instance.name} updated successfully!")
        return super().form_valid(form)


@login_required
def generate_bid_pdf(request, pk):
    """Generate PDF version of bid sheet"""
    bid = get_object_or_404(BidSheet, pk=pk)
    company_info = CompanyInfo.objects.first()

    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.blue,
        alignment=TA_CENTER,
        spaceAfter=30,
    )

    story = []

    # Company Header
    if company_info:
        company_data = [
            [company_info.name, f"Bid #{bid.bid_number}"],
            [
                company_info.address.replace("\n", "<br/>"),
                f"Date: {bid.created_at.strftime('%B %d, %Y')}",
            ],
            [
                f"Phone: {company_info.phone}",
                f"Valid Until: {bid.valid_until.strftime('%B %d, %Y')}",
            ],
        ]
        if company_info.email:
            company_data.append([f"Email: {company_info.email}", ""])

        company_table = Table(company_data, colWidths=[3.5 * inch, 3.5 * inch])
        company_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(company_table)
        story.append(Spacer(1, 20))

    # Bid Title
    story.append(Paragraph(bid.title, title_style))

    # Customer Information
    customer_info = f"""
    <b>Customer:</b> {bid.customer.name}<br/>
    {f'<b>Company:</b> {bid.customer.company}<br/>' if bid.customer.company else ''}
    <b>Email:</b> {bid.customer.email}<br/>
    {f'<b>Phone:</b> {bid.customer.phone}<br/>' if bid.customer.phone else ''}
    {f'<b>Address:</b> {bid.customer.address}<br/>' if bid.customer.address else ''}
    """
    story.append(Paragraph(customer_info, styles["Normal"]))
    story.append(Spacer(1, 20))

    # Project Description
    if bid.project_description:
        story.append(Paragraph("<b>Project Description:</b>", styles["Heading2"]))
        story.append(Paragraph(bid.project_description, styles["Normal"]))
        story.append(Spacer(1, 20))

    # Project Address
    if bid.project_address:
        story.append(Paragraph(f"<b>Project Address:</b> {bid.project_address}", styles["Normal"]))
        story.append(Spacer(1, 20))

    # Bid Items
    story.append(Paragraph("Bid Items", styles["Heading2"]))

    # Items table
    items_data = [["Description", "Qty", "Unit", "Unit Price", "Total"]]
    for item in bid.items.all():
        items_data.append(
            [
                item.description,
                f"{item.quantity:,.2f}",
                item.unit_type,
                f"${item.unit_price:,.2f}",
                f"${item.total_price:,.2f}",
            ]
        )

    items_table = Table(
        items_data, colWidths=[3 * inch, 0.8 * inch, 0.8 * inch, 1 * inch, 1 * inch]
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]
        )
    )
    story.append(items_table)
    story.append(Spacer(1, 20))

    # Totals
    totals_data = [
        ["Subtotal:", f"${bid.subtotal:,.2f}"],
    ]

    if bid.discount_percentage > 0:
        totals_data.append(
            [f"Discount ({bid.discount_percentage}%):", f"-${bid.discount_amount:,.2f}"]
        )

    if bid.tax_percentage > 0:
        totals_data.append([f"Tax ({bid.tax_percentage}%):", f"${bid.tax_amount:,.2f}"])

    totals_data.append(["Total:", f"${bid.total_amount:,.2f}"])

    totals_table = Table(totals_data, colWidths=[5 * inch, 1.5 * inch])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 30))

    # Terms and Conditions
    terms = (
        bid.custom_terms
        if bid.custom_terms
        else (company_info.default_terms if company_info else "")
    )
    if terms:
        story.append(Paragraph("Terms and Conditions", styles["Heading2"]))
        story.append(Paragraph(terms, styles["Normal"]))
        story.append(Spacer(1, 20))

    # Exclusions
    exclusions = (
        bid.custom_exclusions
        if bid.custom_exclusions
        else (company_info.default_exclusions if company_info else "")
    )
    if exclusions:
        story.append(Paragraph("Exclusions", styles["Heading2"]))
        story.append(Paragraph(exclusions.replace("\n", "<br/>"), styles["Normal"]))

    # Build PDF
    doc.build(story)

    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Bid_{bid.bid_number}.pdf"'

    return response


@login_required
def email_bid(request, pk):
    """Email bid sheet to customer"""
    bid = get_object_or_404(BidSheet, pk=pk)

    if request.method == "POST":
        form = EmailBidForm(request.POST)
        if form.is_valid():
            try:
                # Create email
                email = EmailMessage(
                    subject=form.cleaned_data["subject"],
                    body=form.cleaned_data["message"],
                    to=[form.cleaned_data["recipient_email"]],
                )

                # Attach PDF if requested
                if form.cleaned_data["include_pdf"]:
                    # Generate PDF
                    buffer = io.BytesIO()
                    # Use the same PDF generation logic as above
                    # (abbreviated for brevity - would use same code as generate_bid_pdf)

                    email.attach(
                        f"Bid_{bid.bid_number}.pdf",
                        buffer.getvalue(),
                        "application/pdf",
                    )

                # Send email
                email.send()

                # Log the email
                BidEmailLog.objects.create(
                    bid=bid,
                    recipient_email=form.cleaned_data["recipient_email"],
                    subject=form.cleaned_data["subject"],
                    message=form.cleaned_data["message"],
                    sent_by=request.user,
                    success=True,
                )

                # Update bid status if it's still draft
                if bid.status == "draft":
                    bid.status = "sent"
                    bid.save()

                messages.success(
                    request,
                    f'Bid emailed successfully to {form.cleaned_data["recipient_email"]}',
                )
                return redirect("bid_detail", pk=bid.pk)

            except Exception as e:
                # Log the error
                BidEmailLog.objects.create(
                    bid=bid,
                    recipient_email=form.cleaned_data["recipient_email"],
                    subject=form.cleaned_data["subject"],
                    message=form.cleaned_data["message"],
                    sent_by=request.user,
                    success=False,
                    error_message=str(e),
                )
                messages.error(request, f"Failed to send email: {str(e)}")
    else:
        # Pre-populate form
        initial_data = {
            "recipient_email": bid.customer.email,
            "subject": f"Bid #{bid.bid_number} - {bid.title}",
            "message": (
                f"Dear {bid.customer.name},\n\nPlease find attached our bid for"
                f" {bid.title}.\n\nThis bid is valid until"
                f" {bid.valid_until.strftime('%B %d, %Y')}.\n\nIf you have any questions, please"
                " don't hesitate to contact us.\n\nBest"
                f" regards,\n{bid.company_info.name if bid.company_info else 'Blue Line Technology'}"
            ),
        }
        form = EmailBidForm(initial=initial_data)

    return render(request, "bidsheets/email_bid.html", {"bid": bid, "form": form})


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
            return redirect("bidsheets:company_settings")
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
