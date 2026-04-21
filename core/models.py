from django.db import models

class Job(models.Model):
    source = models.CharField(max_length=50)
    source_job_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    job_hash = models.CharField(max_length=64, unique=True) # For deduplication: title + company + location
    
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    skills = models.TextField(blank=True)
    external_apply_link = models.URLField(max_length=1000)
    employment_type = models.CharField(max_length=100, blank=True)
    salary_range = models.CharField(max_length=255, blank=True)
    experience_years = models.CharField(max_length=100, blank=True)
    company_logo = models.URLField(max_length=1000, blank=True)
    posted_date = models.DateTimeField(null=True, blank=True)
    visa_type = models.CharField(max_length=255, blank=True) # e.g., "H-1B, OPT/CPT"
    
    is_published = models.BooleanField(default=True)
    is_reviewing = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company}"
