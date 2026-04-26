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
# from core.scrapers.sources import SimplifyScraper, JobrightScraper, MigrateMateScraper, LinkResolver
from core.scrapers.sources import SimplifyScraper, JobrightScraper, LinkResolver
from core.scrapers.categories import matches_target_titles
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger('sociax_sync')


class ScraperEngine:
    def __init__(self):
        self._last_scraped = 0
        self._last_saved = 0
        self.jobright_stats = {'total': 0, 'internships': 0}

    def run_sync(self, should_continue=None):
        """Run sync: Simplify & Jobright FIRST. (MigrateMate currently disabled)"""
        log.info("🚀 Starting sync cycle...")

        scrapers = [
            SimplifyScraper(),
            JobrightScraper(),
            # MigrateMateScraper(), # Disabled as per user request to avoid blockages
        ]

        total_scraped = 0
        total_saved = 0
        
        round_num = 1
        while True:
            # Check if we should stop
            if should_continue and not should_continue():
                log.info("🛑 Stop signal received. Ending sync.")
                break

            log.info(f"🔄 Pass {round_num}: Fetching all sources in parallel...")
            
            pass_saved = 0
            all_raw_jobs = []
            
            # 1. Parallel Fetch from all sources
            with ThreadPoolExecutor(max_workers=len(scrapers)) as fetch_executor:
                future_to_name = {
                    fetch_executor.submit(scraper.fetch): scraper.__class__.__name__ 
                    for scraper in scrapers
                }
                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        source_jobs = future.result()
                        log.info(f"    📡 {name} returned {len(source_jobs)} raw listings.")
                        all_raw_jobs.extend(source_jobs)
                    except Exception as e:
                        log.error(f"  🛑 {name} fetch error: {e}")

            if not all_raw_jobs:
                log.info("  ⚠️ No jobs found in this pass.")
            else:
                # 2. Filter and Mix
                # Shuffle or just process as they come (all_raw_jobs is already somewhat mixed by parallel completion)
                import random
                random.shuffle(all_raw_jobs)
                
                valid_jobs = []
                for raw in all_raw_jobs:
                    if self._is_job_valid(raw):
                        valid_jobs.append(raw)
                
                log.info(f"    ⭐ Found {len(valid_jobs)} valid jobs after filtering.")

                # 3. Parallel Link Resolution for valid jobs
                if valid_jobs:
                    log.info(f"    🔗 Resolving {len(valid_jobs)} direct links in parallel...")
                    with ThreadPoolExecutor(max_workers=10) as resolver_executor:
                        future_to_job = {
                            resolver_executor.submit(self._resolve_job_link, job): job 
                            for job in valid_jobs
                        }
                        for future in as_completed(future_to_job):
                            if should_continue and not should_continue(): break
                            
                            try:
                                resolved_job = future.result()
                                if self._save_job(resolved_job):
                                    total_saved += 1
                                    pass_saved += 1
                            except Exception as e:
                                log.debug(f"      ❌ Resolve/Save error: {e}")

            log.info(f"  ✅ Pass {round_num} complete. +{pass_saved} jobs saved.")
            
            # Continuous syncing: micro-delay to prevent CPU pegging but keep it moving
            import time
            time.sleep(1)
            
            round_num += 1
            # Continuous syncing: removed the safety cap as requested.

        # Final Dashboard Summary
        self._last_scraped = total_scraped
        self._last_saved = total_saved
        log.info(f"✅ Sync Session Ended: {total_scraped} processed, {total_saved} unique saved.")
        return total_scraped, total_saved

    def _is_job_valid(self, raw):
        """Check filters without resolving links yet."""
        title = (raw.get('title') or '').strip()
        location_raw = (raw.get('location') or 'USA').strip()
        location = clean_location(location_raw)
        url = (raw.get('external_apply_link') or '').strip()
        company = (raw.get('company') or 'Unknown').strip()
        source = raw.get('source', '')

        if not title or not url:
            return False
            
        # 1. Title Match
        if not matches_target_titles(title):
            log.info(f"  ❌ Title mismatch: {title}")
            return False
            
        # 2. US Based
        if not is_us_based(location):
            log.info(f"  ❌ Not US based: {location}")
            return False
            
        # 3. Source-Specific Internship Filtering
        is_intern = 'intern' in title.lower() or raw.get('employment_type') == 'Internship'
        
        # Simplify: Exclude all internships
        if 'Simplify' in source:
            if is_intern:
                log.info(f"  ❌ Simplify Intern Skip: {title}")
                return False
        
        # Jobright: Max 10% internships
        if 'Jobright' in source:
            self.jobright_stats['total'] += 1
            if is_intern:
                # If adding this would exceed 10%, skip it
                current_rate = (self.jobright_stats['internships'] + 1) / self.jobright_stats['total']
                if current_rate > 0.10:
                    # log.debug(f"  ❌ Jobright Intern Rate Skip ({current_rate:.2f})")
                    return False
                self.jobright_stats['internships'] += 1

        # 4. STRICT 48-Hour Date Filter (Requested: "Last 48 hours")
        posted_date = raw.get('posted_date')
        if not posted_date: 
            log.info(f"  ❌ Missing date skip: {title}")
            return False
        
        # Ensure it's aware
        if posted_date.tzinfo is None:
            posted_date = posted_date.replace(tzinfo=tz.utc)

        time_since_posted = timezone.now() - posted_date
        
        # Strictly 48 hours Hard Limit (Requested by User)
        if time_since_posted.total_seconds() > 172800:
            log.info(f"  ❌ Stale skip (>48h): {title}")
            return False
            
        # 5. Duplicate Check (Hash)
        job_hash = generate_job_hash(company, title, location)
        existing = Job.objects.filter(job_hash=job_hash).first()
        if existing:
            if len(existing.description) < 300:
                return True
            return False
            
        log.info(f"  ✅ [STRICT 48H] Valid: {title} ({source})")
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
                date_val = timezone.make_aware(date_val)
            # If it's just a date (midnight), set to end of day to give it a 24h window
            if date_val.hour == 0 and date_val.minute == 0:
                date_val = date_val.replace(hour=23, minute=59, second=59)
            return date_val
        try:
            import dateutil.parser
            dt = dateutil.parser.parse(str(date_val))
            # If it's just a date, set to end of day
            if ' ' not in str(date_val) and ':' not in str(date_val):
                dt = dt.replace(hour=23, minute=59, second=59)
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
