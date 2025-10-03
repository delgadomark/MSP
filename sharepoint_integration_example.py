# Example: Export functionality for SharePoint integration

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import csv
import io


@login_required
def export_projects_csv(request):
    """Export project data for SharePoint import"""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="projects_export.csv"'

    writer = csv.writer(response)
    writer.writerow(["Title", "Status", "Department", "Assigned To", "Created Date", "SLA Hours"])

    # Export your project data
    projects = ProjectCard.objects.all()
    for project in projects:
        writer.writerow(
            [
                project.title,
                project.get_status_display(),
                project.get_department_display(),
                project.assigned_to.get_full_name() if project.assigned_to else "",
                project.created_at.strftime("%Y-%m-%d"),
                project.sla_hours,
            ]
        )

    return response
