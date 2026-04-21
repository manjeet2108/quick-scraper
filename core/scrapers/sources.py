"""
Sociax Sync — 3 Source Scrapers
Only: Simplify Jobs, Jobright.ai, MigrateMate
"""
import re
import json
import logging
import requests
import time
import random
import cloudscraper
from datetime import datetime, timezone as tz
from bs4 import BeautifulSoup

log = logging.getLogger('sociax_sync')

# Setup advanced scraping session
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)
scraper.headers.update({
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
})


# ═══════════════════════════════════════════════════════════
#  1. SIMPLIFY JOBS — GitHub JSON (listings.json)
# ═══════════════════════════════════════════════════════════
class SimplifyScraper:
    """
    Pulls from SimplifyJobs/New-Grad-Positions GitHub repo.
    The repo has a structured JSON file at:
    .github/scripts/listings.json
    Each entry has: title, company_name, url, locations[], sponsorship, 
    date_posted (unix timestamp), active, is_visible, category
    """
    REPOS = [
        ("SimplifyJobs", "New-Grad-Positions", "dev"),
        ("SimplifyJobs", "Summer2026-Internships", "dev"),
    ]

    def fetch(self, query=None):
        jobs = []
        for org, repo, branch in self.REPOS:
            url = f"https://raw.githubusercontent.com/{org}/{repo}/refs/heads/{branch}/.github/scripts/listings.json"
            try:
                log.info(f"    📥 Fetching Simplify: {org}/{repo}")
                time.sleep(random.uniform(1.0, 2.0)) # Delay to prevent bot detection
                resp = scraper.get(url, timeout=30)
                if resp.status_code != 200:
                    log.warning(f"    ⚠️ Simplify {repo} returned {resp.status_code}")
                    continue

                data = json.loads(resp.text)
                log.info(f"    ← Simplify {repo}: {len(data)} total listings")

                for item in data:
                    # Only active and visible jobs
                    if not item.get('active', False):
                        continue

                    title = item.get('title', '').strip()
                    company = item.get('company_name', '').strip()
                    apply_url = item.get('url', '').strip()
                    locations = item.get('locations', [])
                    location_str = ', '.join(locations) if locations else 'USA'
                    sponsorship = item.get('sponsorship', '')
                    category = item.get('category', '')

                    # Parse unix timestamp
                    posted_ts = item.get('date_posted', 0)
                    try:
                        posted_date = datetime.fromtimestamp(posted_ts, tz=tz.utc)
                    except Exception:
                        posted_date = None

                    # Determine visa type from sponsorship field
                    visa_type = ''
                    if sponsorship and 'offers sponsorship' in sponsorship.lower():
                        visa_type = 'H-1B'

                    jobs.append({
                        'source': f'Simplify/{repo}',
                        'source_job_id': item.get('id', ''),
                        'title': title,
                        'company': company,
                        'location': location_str,
                        'description': f"{title} at {company}. Category: {category}. Sponsorship: {sponsorship}.",
                        'external_apply_link': apply_url,
                        'employment_type': 'Full-time',
                        'salary_range': '',
                        'company_logo': '',
                        'posted_date': posted_date,
                        'visa_type': visa_type,
                    })

            except Exception as e:
                log.error(f"    ❌ Simplify {repo} error: {e}")

        log.info(f"    ✅ Simplify total active: {len(jobs)}")
        return jobs


# ═══════════════════════════════════════════════════════════
#  2. JOBRIGHT.AI — GitHub Markdown Tables (README.md)
# ═══════════════════════════════════════════════════════════
class JobrightScraper:
    """
    Pulls from jobright-ai GitHub repos.
    Each repo has a README.md with markdown tables of jobs.
    Format: | Company | Job Title | Location | Apply Link | Date |
    """
    # All 36 repos from jobright-ai (Internships + New Grad)
    REPOS = [
        # Internships
        "2026-Software-Engineer-Internship",
        "2026-Data-Analysis-Internship",
        "2026-Engineer-Internship",
        "2026-Product-Management-Internship",
        "2026-Design-Internship",
        "2026-Business-Analyst-Internship",
        "2026-Marketing-Internship",
        "2026-Account-Internship",
        "2026-Sales-Internship",
        "2026-HR-Internship",
        "2026-Legal-Internship",
        "2026-Education-Internship",
        "2026-Support-Internship",
        "2026-Art-Internship",
        "2026-Management-Internship",
        "2026-Consultant-Internship",
        "2026-Public-Sector-Internship",
        # New Grad
        "2026-Data-Analysis-New-Grad",
        "2026-Engineering-New-Grad",
        "2026-Business-Analyst-New-Grad",
        "2026-Account-New-Grad",
        "2026-Design-New-Grad",
        "2026-Consultant-New-Grad",
        "2026-Support-New-Grad",
        "2026-Marketing-New-Grad",
        "2026-Education-New-Grad",
        "2026-HR-New-Grad",
        "2026-Legal-New-Grad",
        "2026-Art-New-Grad",
        "2026-Management-New-Grad",
    ]

    def fetch(self, query=None):
        jobs = []
        for repo in self.REPOS:
            try:
                url = f"https://raw.githubusercontent.com/jobright-ai/{repo}/refs/heads/main/README.md"
                log.info(f"    📥 Fetching Jobright: {repo}")
                time.sleep(random.uniform(1.5, 3.0)) # Delay to prevent rate limits
                resp = scraper.get(url, timeout=30)
                
                if resp.status_code == 404:
                    # Try master branch
                    url = f"https://raw.githubusercontent.com/jobright-ai/{repo}/refs/heads/master/README.md"
                    time.sleep(random.uniform(1.0, 2.0))
                    resp = scraper.get(url, timeout=30)
                
                if resp.status_code != 200:
                    log.warning(f"    ⚠️ Jobright {repo}: {resp.status_code}")
                    continue

                parsed = self._parse_markdown_table(resp.text, repo)
                jobs.extend(parsed)
                log.info(f"    ← Jobright {repo}: {len(parsed)} jobs")

            except Exception as e:
                log.error(f"    ❌ Jobright {repo}: {e}")

        log.info(f"    ✅ Jobright total: {len(jobs)}")
        return jobs

    def _parse_markdown_table(self, md_text, repo_name):
        """Parse markdown table rows into job dicts."""
        jobs = []
        lines = md_text.split('\n')

        for line in lines:
            # Match table rows: | col1 | col2 | col3 | ...
            if not line.strip().startswith('|'):
                continue
            # Skip header/separator rows
            if '---' in line or 'Company' in line and 'Title' in line:
                continue

            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) < 4:
                continue

            # Typical format: | Date | Company | Title | Location | Link |
            # But format varies. Try to extract intelligently.
            company = ''
            title = ''
            location = ''
            apply_link = ''
            date_str = ''

            # Extract links from markdown [text](url)
            link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'

            for i, cell in enumerate(cells):
                links = re.findall(link_pattern, cell)
                clean = re.sub(link_pattern, r'\1', cell).strip()
                clean = re.sub(r'<[^>]+>', '', clean).strip()  # Remove HTML tags
                clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean) # Remove markdown bold
                clean = clean.replace('↳', '').replace('**', '').replace('[', '').replace(']', '').strip()

                if not clean and not links:
                    continue

                # Date detection (Apr 19, 2026 or similar)
                if re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', clean):
                    date_str = clean
                    continue

                # If cell has a link and no company yet → company
                if links and not company:
                    company = links[0][0]
                    if not apply_link and links[0][1].startswith('http'):
                        apply_link = links[0][1]
                    continue

                # Title detection (contains role keywords or has apply link)
                if not title:
                    if links:
                        title = links[0][0]
                        apply_link = links[0][1] if links[0][1].startswith('http') else apply_link
                    else:
                        title = clean
                    continue

                # Location 
                if not location and clean:
                    location = clean
                    continue

                # Remaining links might be apply links
                if links and not apply_link:
                    for text, url in links:
                        if url.startswith('http'):
                            apply_link = url
                            break

            if title and company:
                jobs.append({
                    'source': f'Jobright/{repo_name}',
                    'source_job_id': f"jr-{hash(title + company) % 100000000}",
                    'title': title,
                    'company': company,
                    'location': location or 'USA',
                    'description': f"{title} at {company}. Source: Jobright.ai ({repo_name})",
                    'external_apply_link': apply_link or '',
                    'employment_type': 'Internship' if 'Internship' in repo_name else 'Full-time',
                    'salary_range': '',
                    'company_logo': '',
                    'posted_date': self._parse_date(date_str),
                    'visa_type': '',
                })

        return jobs

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            # Try "Apr 19" format (assume current year)
            from datetime import datetime
            dt = datetime.strptime(f"{date_str}, 2026", "%b %d, %Y")
            return dt.replace(tzinfo=tz.utc)
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════
#  3. MIGRATEMATE — Web Scrape HTML 
# ═══════════════════════════════════════════════════════════
class MigrateMateScraper:
    """
    Scrapes migratemate.co visa sponsorship jobs.
    Pages: /visa-sponsorship-jobs/h1b, /opt, /tn, etc.
    """
    VISA_PAGES = [
        ('h1b', 'H-1B'),
        ('opt', 'OPT/CPT'),
        ('tn', 'TN'),
        ('green-card', 'Green Card'),
    ]

    def fetch(self, query=None):
        jobs = []
        for slug, visa_type in self.VISA_PAGES:
            try:
                url = f"https://migratemate.co/visa-sponsorship-jobs/{slug}"
                log.info(f"    📥 Fetching MigrateMate: {visa_type}")
                # Stronger delay for aggressive bot protections (Cloudflare)
                time.sleep(random.uniform(3.0, 5.0)) 
                
                # Cloudscraper specifically handles MigrateMate Cloudflare challenge
                resp = scraper.get(url, timeout=30)
                
                if resp.status_code == 429:
                    log.warning(f"    ⚠️ MigrateMate rate limited on {slug}, skipping")
                    continue
                if resp.status_code != 200:
                    log.warning(f"    ⚠️ MigrateMate {slug}: {resp.status_code}")
                    continue

                parsed = self._parse_html(resp.text, visa_type)
                jobs.extend(parsed)
                log.info(f"    ← MigrateMate {visa_type}: {len(parsed)} jobs")

            except Exception as e:
                log.error(f"    ❌ MigrateMate {slug}: {e}")

        log.info(f"    ✅ MigrateMate total: {len(jobs)}")
        return jobs

    def _parse_html(self, html, visa_type):
        """Parse MigrateMate job listing HTML."""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')

        # Look for job cards/links — structure varies, try common patterns
        # Try finding job listing containers
        for card in soup.select('a[href*="/jobs/"], a[href*="/job/"], .job-card, .job-listing, tr'):
            title = ''
            company = ''
            location = ''
            apply_link = ''

            # Try to extract from link
            if card.name == 'a':
                title = card.get_text(strip=True)
                href = card.get('href', '')
                if href.startswith('/'):
                    apply_link = f"https://migratemate.co{href}"
                elif href.startswith('http'):
                    apply_link = href
            elif card.name == 'tr':
                cells = card.find_all('td')
                if len(cells) >= 2:
                    link = cells[0].find('a')
                    if link:
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        apply_link = href if href.startswith('http') else f"https://migratemate.co{href}"
                    if len(cells) >= 2:
                        company = cells[1].get_text(strip=True)
                    if len(cells) >= 3:
                        location = cells[2].get_text(strip=True)

            if not title or len(title) < 5:
                continue

            # Try to extract company from title if not found
            if not company and ' at ' in title:
                parts = title.split(' at ', 1)
                title = parts[0].strip()
                company = parts[1].strip()

            jobs.append({
                'source': 'MigrateMate',
                'source_job_id': f"mm-{hash(title + company) % 100000000}",
                'title': title,
                'company': company or 'Unknown',
                'location': location or 'USA',
                'description': f"{title}. Visa: {visa_type}. Source: MigrateMate.co",
                'external_apply_link': apply_link,
                'employment_type': 'Full-time',
                'salary_range': '',
                'company_logo': '',
                'posted_date': None,
                'visa_type': visa_type,
            })

        return jobs
