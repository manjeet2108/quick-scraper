from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_date', 'visa_type', 'is_published')
    list_filter = ('source', 'visa_type', 'is_published', 'is_archived')
    search_fields = ('title', 'company', 'description')
