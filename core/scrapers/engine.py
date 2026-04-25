"""
Sociax Sync Engine — 3 Sources Only
Simplify Jobs | Jobright.ai | MigrateMate
"""
import os
import logging
from datetime import datetime, timedelta, timezone as tz
from django.utils import timezone
from core.models import Job
from core.utils import (
    clean_text, is_visa_sponsored, is_entry_level,
    is_us_based, is_direct_link, generate_job_hash,
    clean_location, get_favicon_url, fetch_full_description,
    extract_job_metadata
)
from core.scrapers.sources import SimplifyScraper, JobrightScraper, MigrateMateScraper, LinkResolver
from core.scrapers.categories import matches_target_titles
from concurrent.futures import ThreadPoolExecutor, as_completed
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
            # MigrateMateScraper(),
        ]

        total_scraped = 0
        total_saved = 0
        target_new_jobs = 100
        max_rounds = 3
        
        for round_num in range(1, max_rounds + 1):
            if total_saved >= target_new_jobs:
                log.info(f"🎯 Target reached ({total_saved} jobs). Ending sync early.")
                break
            
            if round_num > 1:
                log.info(f"🔄 Round {round_num}: Attempting to find more jobs...")

            for scraper in scrapers:
                name = scraper.__class__.__name__
                try:
                    log.info(f"  📡 Starting Fetch: {name} (Round {round_num})...")
                    raw_jobs = scraper.fetch()
                    
                    # 1. Filter: US-Based & 24h & Duplicate in DB
                    log.info(f"    🔍 Pre-filtering {len(raw_jobs)} jobs...")
                    valid_for_this = []
                    for raw in raw_jobs:
                        if self._is_job_valid(raw):
                            valid_for_this.append(raw)
                    
                    if not valid_for_this:
                        log.info(f"    ⏭️ No new/relevant jobs found in {name}.")
                        continue

                    # 2. Parallel Link Resolution (The Bottleneck!)
                    log.info(f"    🔗 Resolving {len(valid_for_this)} direct links in parallel...")
                    with ThreadPoolExecutor(max_workers=8) as resolver_executor:
                        future_to_job = {
                            resolver_executor.submit(self._resolve_job_link, job): job 
                            for job in valid_for_this
                        }
                        for future in as_completed(future_to_job):
                            resolved_job = future.result()
                            # 3. Final Save
                            try:
                                if self._save_job(resolved_job):
                                    total_saved += 1
                            except Exception as e:
                                log.debug(f"  ❌ Save error: {e}")

                    total_scraped += len(raw_jobs)
                    log.info(f"  ← {name} Summary: {len(raw_jobs)} found | +{len(valid_for_this)} processed.")

                except Exception as e:
                    log.warning(f"  🛑 {name} blocked or error: {e}. Switching to next source...")
                    continue

        # Final Dashboard Summary
        self._last_scraped = total_scraped
        self._last_saved = total_saved
        log.info(f"✅ Sync Cycle Complete: {total_scraped} processed, {total_saved} unique saved.")
        return total_scraped, total_saved

    def _is_job_valid(self, raw):
        """Check filters without resolving links yet."""
        title = (raw.get('title') or '').strip()
        location_raw = (raw.get('location') or 'USA').strip()
        location = clean_location(location_raw)
        url = (raw.get('external_apply_link') or '').strip()
        company = (raw.get('company') or 'Unknown').strip()

        if not title or not url:
            return False
            
        # 1. Title Match
        if not matches_target_titles(title):
            return False
            
        # 2. US Based
        if not is_us_based(location):
            return False
            
        # 3. Date Filter (24h)
        posted_date = raw.get('posted_date')
        if not posted_date: 
            return False
        
        # Ensure it's aware
        if posted_date.tzinfo is None:
            posted_date = posted_date.replace(tzinfo=tz.utc)

        time_since_posted = timezone.now() - posted_date
        if time_since_posted.total_seconds() > 86400:
            return False
            
        # 4. Duplicate Check (Hash)
        job_hash = generate_job_hash(company, title, location)
        existing = Job.objects.filter(job_hash=job_hash).first()
        if existing:
            # If the job exists BUT description is too short, allow it through for an update
            if len(existing.description) < 300:
                log.debug(f"  📝 Allowing update for existing job: {title}")
                return True
            return False
            
        return True

    def _resolve_job_link(self, raw):
        """Worker for parallel link resolution."""
        url = raw.get('external_apply_link', '')
        
        if any(x in url for x in ['jobright.ai', 'migratemate.co', 'simplify.jobs', 'github.com']):
            try:
                direct_link = LinkResolver.resolve_single(url, LinkResolver.session)
                if direct_link:
                    raw['external_apply_link'] = direct_link
            except:
                pass
        return raw

    def _save_job(self, raw):
        """Final save to database."""
        title = raw.get('title', '').strip()
        company = raw.get('company', 'Unknown').strip()
        url = raw.get('external_apply_link', '')
        location = clean_location(raw.get('location', 'USA'))
        desc = raw.get('description', '')
        posted_date = raw.get('posted_date')
        
        # Detect visa sponsorship 
        visa_type = raw.get('visa_type', '')
        if not visa_type:
            visa_type = is_visa_sponsored(title, desc) or ''

        # Resolve Logo
        logo = raw.get('company_logo')
        if not logo:
            logo = get_favicon_url(company, url)

        # Extract dynamic metadata
        meta = extract_job_metadata(title, desc)
        job_hash = generate_job_hash(company, title, location)

        # Attempt to fetch full description if current one is too short
        if len(desc) < 300 and is_direct_link(url):
            log.info(f"    📄 Fetching full description: {company}")
            full_desc = fetch_full_description(url)
            if full_desc and len(full_desc) > len(desc):
                desc = full_desc

        # Save with Logo & Description Update Support
        job, created = Job.objects.get_or_create(
            job_hash=job_hash,
            defaults={
                'source': raw.get('source', 'Unknown'),
                'source_job_id': str(raw.get('source_job_id', '')),
                'title': title,
                'company': company,
                'location': location,
                'description': desc,
                'skills': self._derive_skills(desc),
                'external_apply_link': url,
                'employment_type': raw.get('employment_type') if raw.get('employment_type') else meta.get('employment_type', 'Full-time'),
                'salary_range': raw.get('salary_range') if raw.get('salary_range') else meta.get('salary_range', ''),
                'experience_years': meta.get('experience_years', 'Not Specified'),
                'company_logo': logo,
                'posted_date': posted_date,
                'visa_type': visa_type,
            }
        )
        
        # Update logic for existing jobs
        updated_fields = []
        if not created:
            if not job.company_logo and logo:
                job.company_logo = logo
                updated_fields.append('company_logo')
            
            # If current description is a placeholder and we have a real one, update it
            if len(job.description) < 300 and len(desc) >= 300:
                job.description = desc
                job.skills = self._derive_skills(desc)
                updated_fields.extend(['description', 'skills'])
            
            if updated_fields:
                job.save(update_fields=updated_fields)
            
        return True


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
