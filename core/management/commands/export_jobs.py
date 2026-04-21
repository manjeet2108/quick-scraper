import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import Job

class Command(BaseCommand):
    help = 'Exports jobs added in the last 24 hours to a CSV file.'

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/jobs_export_{timestamp}.csv"
        os.makedirs("exports", exist_ok=True)

        # Get jobs from the last 24 hours
        from django.utils import timezone
        from datetime import timedelta
        yesterday = timezone.now() - timedelta(days=1)
        jobs = Job.objects.filter(created_at__gte=yesterday)

        fields = [
            'title', 'company', 'location', 'description', 'skills', 
            'external_apply_link', 'employment_type', 'salary_range', 
            'experience_years', 'company_logo', 'is_published', 
            'is_reviewing', 'is_archived', 'posted_date'
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for job in jobs:
                writer.writerow({
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'skills': job.skills,
                    'external_apply_link': job.external_apply_link,
                    'employment_type': job.employment_type,
                    'salary_range': job.salary_range,
                    'experience_years': job.experience_years,
                    'company_logo': job.company_logo,
                    'is_published': 1 if job.is_published else 0,
                    'is_reviewing': 1 if job.is_reviewing else 0,
                    'is_archived': 1 if job.is_archived else 0,
                    'posted_date': job.posted_date.strftime("%Y-%m-%d") if job.posted_date else ""
                })

        self.stdout.write(self.style.SUCCESS(f"Successfully exported {len(jobs)} jobs to {filename}"))
