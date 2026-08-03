import csv
import datetime
import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Max
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import AlignmentForm, ReportFilterForm
from .models import Alignment, Truck

User = get_user_model()


def staff_required(view_func):
    """Only staff (admin) accounts may access user management."""
    return user_passes_test(lambda u: u.is_staff, login_url='dashboard')(view_func)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    today = timezone.localdate()

    total_alignments = Alignment.objects.count()

    this_month_count = Alignment.objects.filter(
        alignment_date__year=today.year,
        alignment_date__month=today.month,
    ).count()

    # Overdue trucks: last alignment for the truck was more than 90 days ago.
    cutoff = today - datetime.timedelta(days=90)
    last_alignment_per_truck = (
        Alignment.objects.values('truck_id')
        .annotate(last_date=Max('alignment_date'))
    )
    overdue_trucks = sum(
        1 for row in last_alignment_per_truck if row['last_date'] and row['last_date'] < cutoff
    )

    avg_mileage = Alignment.objects.aggregate(avg=Avg('mileage'))['avg'] or 0

    recent_alignments = Alignment.objects.all()[:10]

    by_tech = (
        Alignment.objects.values('tech_name')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    by_truck = (
        Alignment.objects.values('truck_id')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    context = {
        'total_alignments': total_alignments,
        'this_month_count': this_month_count,
        'overdue_trucks': overdue_trucks,
        'avg_mileage': round(avg_mileage, 1),
        'recent_alignments': recent_alignments,
        'tech_labels': [row['tech_name'] for row in by_tech],
        'tech_data': [row['total'] for row in by_tech],
        'truck_labels': [row['truck_id'] for row in by_truck],
        'truck_data': [row['total'] for row in by_truck],
    }
    return render(request, 'alignments/dashboard.html', context)


# ---------------------------------------------------------------------------
# Add / Edit / Delete
# ---------------------------------------------------------------------------
def _truck_trailer_map():
    return {t.truck_id: (t.trailer_id or '') for t in Truck.objects.filter(active=True)}


@login_required
def add_alignment(request):
    if request.method == 'POST':
        form = AlignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Alignment record was added successfully.")
            return redirect('dashboard')
    else:
        form = AlignmentForm()
    return render(request, 'alignments/add_alignment.html', {
        'form': form,
        'truck_trailer_map_json': json.dumps(_truck_trailer_map()),
    })


@login_required
def edit_alignment(request, pk):
    alignment = get_object_or_404(Alignment, pk=pk)
    if request.method == 'POST':
        form = AlignmentForm(request.POST, instance=alignment)
        if form.is_valid():
            form.save()
            messages.success(request, "Alignment record was updated successfully.")
            return redirect('reports')
    else:
        form = AlignmentForm(instance=alignment)
    return render(
        request,
        'alignments/add_alignment.html',
        {
            'form': form,
            'is_edit': True,
            'alignment': alignment,
            'truck_trailer_map_json': json.dumps(_truck_trailer_map()),
        },
    )


@login_required
def delete_alignment(request, pk):
    alignment = get_object_or_404(Alignment, pk=pk)
    if request.method == 'POST':
        alignment.delete()
        messages.success(request, "Alignment record was deleted.")
        return redirect('reports')
    return render(request, 'alignments/alignment_confirm_delete.html', {'alignment': alignment})


# ---------------------------------------------------------------------------
# Reports / filtering / export
# ---------------------------------------------------------------------------
def _filtered_queryset(request):
    tech_choices = list(
        Alignment.objects.order_by('tech_name')
        .values_list('tech_name', 'tech_name')
        .distinct()
    )
    truck_choices = list(
        Alignment.objects.order_by('truck_id')
        .values_list('truck_id', 'truck_id')
        .distinct()
    )

    form = ReportFilterForm(
        request.GET or None,
        tech_choices=tech_choices,
        truck_choices=truck_choices,
    )

    queryset = Alignment.objects.all()

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        tech_name = form.cleaned_data.get('tech_name')
        truck_id = form.cleaned_data.get('truck_id')

        if start_date:
            queryset = queryset.filter(alignment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(alignment_date__lte=end_date)
        if tech_name:
            queryset = queryset.filter(tech_name=tech_name)
        if truck_id:
            queryset = queryset.filter(truck_id=truck_id)

    return form, queryset


@login_required
def reports(request):
    form, queryset = _filtered_queryset(request)
    context = {
        'form': form,
        'alignments': queryset,
        'result_count': queryset.count(),
        'querystring': request.GET.urlencode(),
    }
    return render(request, 'alignments/reports.html', context)


@login_required
def export_csv(request):
    _, queryset = _filtered_queryset(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alignments_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Truck ID', 'Trailer ID', 'Date', 'Time', 'Mileage', 'Technician', 'Created At',
    ])
    for a in queryset:
        writer.writerow([
            a.truck_id,
            a.trailer_id or '',
            a.alignment_date,
            a.alignment_time,
            a.mileage,
            a.tech_name,
            a.created_at,
        ])
    return response


@login_required
def export_pdf(request):
    import os

    from django.conf import settings
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    form, queryset = _filtered_queryset(request)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="alignments_report.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=2,
        textColor=colors.HexColor('#111315'),
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#555555'), spaceAfter=10,
    )

    elements = []

    logo_path = os.path.join(
        settings.BASE_DIR, 'alignments', 'static', 'alignments', 'img', 'logo-black.png'
    )
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.4 * inch, height=1.4 * inch)
        logo.hAlign = 'LEFT'
        elements.append(logo)
        elements.append(Spacer(1, 6))

    elements.append(Paragraph("D&amp;A Hauliers Ltd &mdash; Truck Alignment Report", title_style))
    elements.append(Paragraph(
        f"Generated {timezone.localtime().strftime('%B %d, %Y %I:%M %p')} &mdash; "
        f"{queryset.count()} record(s)",
        subtitle_style,
    ))

    filter_bits = []
    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            filter_bits.append(f"From: {form.cleaned_data['start_date']}")
        if form.cleaned_data.get('end_date'):
            filter_bits.append(f"To: {form.cleaned_data['end_date']}")
        if form.cleaned_data.get('tech_name'):
            filter_bits.append(f"Technician: {form.cleaned_data['tech_name']}")
        if form.cleaned_data.get('truck_id'):
            filter_bits.append(f"Truck: {form.cleaned_data['truck_id']}")
    if filter_bits:
        elements.append(Paragraph("Filters &mdash; " + " | ".join(filter_bits), subtitle_style))

    elements.append(Spacer(1, 8))

    table_data = [['Truck ID', 'Trailer ID', 'Date', 'Time', 'Mileage', 'Technician']]
    for a in queryset:
        table_data.append([
            a.truck_id,
            a.trailer_id or '—',
            str(a.alignment_date),
            a.alignment_time.strftime('%H:%M'),
            f"{a.mileage:,} mi",
            a.tech_name,
        ])

    if len(table_data) == 1:
        table_data.append(['No records match the selected filters.', '', '', '', '', ''])

    table = Table(table_data, repeatRows=1, colWidths=[1.6 * inch, 1.6 * inch, 1.4 * inch, 1.2 * inch, 1.4 * inch, 2.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111315')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6f9')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dde3ea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    return response


@login_required
def export_excel(request):
    import pandas as pd

    _, queryset = _filtered_queryset(request)

    data = [{
        'Truck ID': a.truck_id,
        'Trailer ID': a.trailer_id or '',
        'Date': a.alignment_date,
        'Time': a.alignment_time,
        'Mileage': a.mileage,
        'Technician': a.tech_name,
        'Created At': a.created_at.replace(tzinfo=None) if a.created_at else '',
    } for a in queryset]

    df = pd.DataFrame(data, columns=[
        'Truck ID', 'Trailer ID', 'Date', 'Time', 'Mileage', 'Technician', 'Created At',
    ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="alignments_export.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alignments')
        worksheet = writer.sheets['Alignments']
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 4, 40)

    return response


# ---------------------------------------------------------------------------
# User management (staff/admin only)
# ---------------------------------------------------------------------------
@staff_required
def user_management(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_user':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            is_staff = request.POST.get('is_staff') == 'on'

            if not username or not password:
                messages.error(request, "Username and password are required.")
            elif User.objects.filter(username=username).exists():
                messages.error(request, f"A user named '{username}' already exists.")
            elif len(password) < 6:
                messages.error(request, "Password must be at least 6 characters.")
            else:
                User.objects.create_user(username=username, password=password, is_staff=is_staff)
                messages.success(request, f"User '{username}' was created.")
            return redirect('user_management')

        elif action == 'toggle_active':
            user_id = request.POST.get('user_id')
            target = get_object_or_404(User, pk=user_id)
            if target == request.user:
                messages.error(request, "You can't deactivate your own account.")
            else:
                target.is_active = not target.is_active
                target.save()
                messages.success(
                    request,
                    f"User '{target.username}' was {'activated' if target.is_active else 'deactivated'}."
                )
            return redirect('user_management')

        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            target = get_object_or_404(User, pk=user_id)
            if target == request.user:
                messages.error(request, "You can't delete your own account.")
            else:
                target.delete()
                messages.success(request, "User was deleted.")
            return redirect('user_management')

    users = User.objects.all().order_by('username')
    return render(request, 'alignments/user_management.html', {'users': users})
