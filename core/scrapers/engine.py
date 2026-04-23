"""
Sociax Sync Engine — 3 Sources Only
Simplify Jobs | Jobright.ai | MigrateMate
"""
import os
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from core.models import Job
from core.utils import (
    clean_text, is_visa_sponsored, is_entry_level,
    is_us_based, is_direct_link, generate_job_hash,
    clean_location, get_favicon_url, fetch_full_description,
    extract_job_metadata
)
from core.scrapers.sources import SimplifyScraper, JobrightScraper, MigrateMateScraper
from core.scrapers.categories import matches_target_titles
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger('sociax_sync')


class ScraperEngine:
    def __init__(self):
        self._last_scraped = 0
        self._last_saved = 0

    def run_sync(self):
        """Run sync: Simplify & Jobright FIRST, MigrateMate LAST."""
        log.info("🚀 Starting sync cycle...")

        # Order matters: Reliable sources first
        scrapers = [
            SimplifyScraper(),
            JobrightScraper(),
            MigrateMateScraper(),
        ]

        total_scraped = 0
        total_saved = 0

        for scraper in scrapers:
            name = scraper.__class__.__name__
            try:
                log.info(f"  📡 Syncing {name}...")
                raw_jobs = scraper.fetch()
                count = len(raw_jobs)
                
                scraped_for_this = 0
                saved_for_this = 0
                
                for raw in raw_jobs:
                    scraped_for_this += 1
                    if self._process_job(raw):
                        saved_for_this += 1

                total_scraped += scraped_for_this
                total_saved += saved_for_this
                
                if count > 0 or "MigrateMate" not in name:
                    log.info(f"  ← {name} Finished: {scraped_for_this} found, {saved_for_this} new.")

            except Exception as e:
                log.error(f"  ❌ {name} encountered an error: {e}")

        # Final Dashboard Summary
        self._last_scraped = total_scraped
        self._last_saved = total_saved
        log.info(f"✅ Full Sync Complete: {total_scraped} total scraped, {total_saved} new saved.")
        return total_scraped, total_saved

    def _process_job(self, raw):
        """Apply filters and save if passes."""
        title = (raw.get('title') or '').strip()
        desc = (raw.get('description') or '').strip()
        location_raw = (raw.get('location') or 'USA').strip()
        location = clean_location(location_raw)
        url = (raw.get('external_apply_link') or '').strip()
        company = (raw.get('company') or 'Unknown').strip()

        if not title or not url:
            return False

        # Filter: US Only
        if not is_us_based(location):
            return False

        # Detect visa sponsorship (from source data OR description)
        visa_type = raw.get('visa_type', '')
        if not visa_type:
            visa_type = is_visa_sponsored(title, desc) or ''

        # Deduplication (EARLY CHECK to save time)
        job_hash = generate_job_hash(title, company, location)
        if Job.objects.filter(job_hash=job_hash).exists():
            return False

        # Filter: Target Job Titles Only (Anil's Custom List)
        if not matches_target_titles(title):
            return False

        # Parse date — STRICT: no date = no save
        posted_date = self._parse_date(raw.get('posted_date'))
        if posted_date is None:
            log.debug(f"  ⏭️ Skipped (no date): {title} at {company}")
            return False
        
        # Filter: 24 Hours Only — STRICT for all 3 sources
        time_since_posted = timezone.now() - posted_date
        if time_since_posted.total_seconds() > 86400:
            return False

        # Resolve Logo
        logo = raw.get('company_logo')
        if not logo:
            logo = get_favicon_url(company, url)

        # Extract dynamic description (Expensive - only do if job is new and relevant)
        if len(desc) < 300:
            fetched_desc = fetch_full_description(url)
            if fetched_desc:
                desc = fetched_desc

        # Extract dynamic metadata
        meta = extract_job_metadata(title, desc)

        # Save
        try:
            job = Job.objects.create(
                source=raw.get('source', 'Unknown'),
                source_job_id=str(raw.get('source_job_id', '')),
                job_hash=job_hash,
                title=title,
                company=company,
                location=location,
                description=desc,
                skills=self._derive_skills(desc),
                external_apply_link=url,
                employment_type=raw.get('employment_type') if raw.get('employment_type') else meta.get('employment_type', 'Full-time'),
                salary_range=raw.get('salary_range') if raw.get('salary_range') else meta.get('salary_range', ''),
                experience_years=meta.get('experience_years', 'Not Specified'),
                company_logo=logo,
                posted_date=posted_date,
                visa_type=visa_type,
            )
            return True

        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                log.debug(f"  ⏭️ Skipped (Existing ID/Hash): {title}")
            else:
                log.error(f"  ❌ Save error: {e}")
            return False

    def _derive_skills(self, desc):
        if not desc:
            return ''
        skills = [
            "Python", "JavaScript", "React", "Node.js", "Java", "AWS", "SQL",
            "Django", "Next.js", "Docker", "Kubernetes", "TypeScript", "Go",
            "C++", "Ruby", "PHP", "Vue.js", "Angular", "MongoDB", "PostgreSQL",
            "Redis", "GraphQL", "REST API", "Git", "Linux", "Azure", "GCP",
            "TensorFlow", "PyTorch", "Machine Learning"
        ]
        desc_lower = desc.lower()
        found = [s for s in skills if s.lower() in desc_lower]
        return ", ".join(found)

    def _parse_date(self, date_val):
        """Parse date value. Returns None if unparseable — job will be skipped."""
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            if date_val.tzinfo is None:
                return timezone.make_aware(date_val)
            return date_val
        try:
            import dateutil.parser
            dt = dateutil.parser.parse(str(date_val))
            if dt.tzinfo is None:
                return timezone.make_aware(dt)
            return dt
        except Exception:
            return None

    def remove_expired_jobs(self, days=30):
        """Archive jobs older than N days."""
        cutoff = timezone.now() - timedelta(days=days)
        expired = Job.objects.filter(posted_date__lt=cutoff, is_archived=False)
        count = expired.update(is_archived=True, is_published=False)
        if count:
            log.info(f"  🗂️ Archived {count} expired jobs.")
