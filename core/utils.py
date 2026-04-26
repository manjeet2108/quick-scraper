import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse
import cloudscraper
import time
import random
from bs4 import BeautifulSoup
import json

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

def clean_text(text):
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', ' ', text)
    # Remove extra whitespace
    return ' '.join(text.split())

def is_visa_sponsored(title, description):
    visa_keywords = [
        r'h-?1b', r'opt', r'cpt', r'tn visa', r'green card', r'j-?1', 
        r'visa sponsorship', r'sponsorship available', r'sponsorship provided',
        r'sponsorship is available'
    ]
    content = (title + " " + description).lower()
    found = []
    for kw in visa_keywords:
        if re.search(kw, content):
            found.append(kw.replace(r'?', ''))
    return ", ".join(set(found)) if found else None

def is_entry_level(title, description):
    entry_keywords = [
        r'junior', r'associate', r'entry[ -]level', r'new grad', r'intern', r'apprentice',
        r'0-?1 year', r'1-?2 years', r'0-?3 years', r'0-?5 years', r'years of experience:? [0-5]'
    ]
    exclude_keywords = [
        r'senior', r'lead', r'staff', r'principal', r'vp', r'director', r'manager', r'head of'
    ]
    
    title_lower = title.lower()
    description_lower = description.lower()
    
    # Check for entry level keywords in title or description
    is_entry = False
    for kw in entry_keywords:
        if re.search(kw, title_lower) or re.search(kw, description_lower):
            is_entry = True
            break
            
    # Check for exclusions in title (exclusions in description are tricky as they might list requirements for others)
    for kw in exclude_keywords:
        if re.search(kw, title_lower):
            # Special case: "Junior Product Manager" might be okay, but "Senior" is not.
            if "junior" not in title_lower:
                return False
                
    return is_entry

def clean_location(location):
    if not location:
        return "Remote / Unknown"
    
    # Remove things like `#5997` or `Corp`
    loc = re.sub(r'#\d+', '', location)
    loc = re.sub(r'\bCorp\b', '', loc, flags=re.IGNORECASE)
    
    # If it is US-FL-Orlando pattern
    m = re.search(r'US-([A-Z]{2})-(.*)', loc, re.IGNORECASE)
    if m:
        loc = f"{m.group(2).replace('-', ' ').title()}, {m.group(1).upper()}"
        
    loc = ' '.join(loc.split()).strip(', ')
    return loc

def get_favicon_url(company_name, apply_url=''):
    """Get a high-res favicon URL from the company website or generic domain."""
    domain = ""
    # List of common ATS domains to ignore for favicon checking
    ats_domains = [
        'greenhouse.io', 'lever.co', 'workday.com', 'myworkdayjobs.com',
        'ashbyhq.com', 'icims.com', 'taleo.net', 'bamboohr.com', 'smartrecruiters.com',
        'jobright.ai', 'simplify.jobs', 'migratemate.co'
    ]
    
    if apply_url:
        try:
            netloc = urlparse(apply_url).netloc.lower()
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            
            is_ats = any(ats in netloc for ats in ats_domains)
            if not is_ats and netloc:
                domain = netloc
        except Exception:
            pass
            
    if not domain:
        # Fallback: synthesize a .com domain from the company name
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', str(company_name)).lower()
        if clean_name:
            domain = f"{clean_name}.com"
        else:
            domain = "example.com"
            
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

def is_us_based(location):
    if not location:
        return False
    
    # Block list for international keywords
    blocked = ['australia', 'uk', 'united kingdom', 'india', 'canada', 'germany', 'france', 'europe', 'asia', 'americas']
    loc_lower = location.lower()
    
    for b in blocked:
        if b in loc_lower:
            # Special case: allow if it explicitly says "Remote (US)" or similar
            if 'remote' in loc_lower and ('us' in loc_lower or 'usa' in loc_lower):
                continue
            return False

    us_keywords = [
        'usa', 'united states', 'us', 'remote', 'san francisco', 'sf', 'new york', 'nyc',
        'austin', 'seattle', 'chicago', 'boston', 'la', 'los angeles', 'dc', 'washington dc',
        'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy'
    ]
    # Check for US state codes (e.g., CA, NY, TX)
    state_codes = r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b'
    
    if any(kw in loc_lower for kw in us_keywords):
        return True
    if re.search(state_codes, location.upper()):
        return True
    return False

def is_direct_link(url):
    blocked_domains = [
        'linkedin.com', 'glassdoor.com', 'indeed.com', 'ziprecruiter.com', 'monster.com',
        'crunchbase.com', 'prnewswire.com', 'businesswire.com', 'facebook.com', 'twitter.com',
        'x.com', 'instagram.com', 'decrypt.co', 'alleywatch.com'
    ]
    for domain in blocked_domains:
        if domain in url.lower():
            return False
    return True

def generate_job_hash(title, company, location):
    data = f"{title}|{company}|{location}".lower().strip()
    return hashlib.md5(data.encode()).hexdigest()

def extract_job_metadata(title, desc):
    metadata = {}
    combined = f"{title}\n{desc}".lower()

    # 1. Employment Type
    if re.search(r'\b(intern|internship|co-op)\b', combined):
        metadata['employment_type'] = 'Internship'
    elif re.search(r'\bpart[- ]time\b', combined):
        metadata['employment_type'] = 'Part-time'
    elif re.search(r'\b(contract|contractor|freelance|temp)\b', combined):
        metadata['employment_type'] = 'Contract'
    else:
        metadata['employment_type'] = 'Full-time'

    # 2. Experience Years
    exp_matches = re.finditer(r'(\d+)\s*(?:-|to)\s*(\d+)\s*\+?\s*years?(?:\s+of\s+experience)?|\b(\d+)\+?\s*years?(?:\s+of\s+experience)?', combined)
    found_years = []
    for match in exp_matches:
        if match.group(1) and match.group(2):
            found_years.append(int(match.group(1)))
            found_years.append(int(match.group(2)))
        elif match.group(3):
            found_years.append(int(match.group(3)))

    valid_years = [y for y in found_years if y < 20] # Sanity check to avoid matching years like 2026
    
    if valid_years:
        min_yr = min(valid_years)
        max_yr = max(valid_years)
        if min_yr == max_yr:
            if min_yr == 0:
                metadata['experience_years'] = 'Entry Level'
            else:
                metadata['experience_years'] = f"{min_yr}+ years"
        elif max_yr - min_yr <= 7:
            metadata['experience_years'] = f"{min_yr}-{max_yr} years"
        else:
            metadata['experience_years'] = f"{min_yr}+ years"
    else:
        if is_entry_level(title, desc):
            metadata['experience_years'] = 'Entry Level'
        else:
            metadata['experience_years'] = 'Not Specified'

    # 3. Salary Range
    salary_regexes = [
        # $100,000 to $150,000 /yr
        r'\$[\d,]+\s*(?:-|to)\s*\$[\d,]+\s*(?:/yr|/year|per year|annually)?',
        # $100k - $150k
        r'\$[\d,]+[kK]?\s*(?:-|to)\s*\$[\d,]+[kK]?',
        # $50 - $80 /hr
        r'\$[\d.]+\s*(?:-|to)\s*\$[\d.]+\s*(?:/hr|/hour|per hour|an hour|/h)'
    ]
    salary = ""
    for regex in salary_regexes:
        match = re.search(regex, desc, re.IGNORECASE)
        if match:
            salary = match.group(0).strip()
            # Clean up the format
            salary = re.sub(r'(?i)\s*(/yr|/year|per year|annually)\s*', ' /yr', salary)
            salary = re.sub(r'(?i)\s*(/hr|/hour|per hour|an hour|/h)\s*', ' /hr', salary)
            break
            
    # Try one more specifically for UK/Europe formats if no $
    if not salary:
        match = re.search(r'£[\d,]+[kK]?\s*(?:-|to)\s*£[\d,]+[kK]?', desc, re.IGNORECASE)
        if match:
            salary = match.group(0).strip()
            
    if salary:
        metadata['salary_range'] = salary
    else:
        metadata['salary_range'] = 'Not Specified'

    return metadata

def fetch_full_description(url):
    """
    Dynamically fetch the full job description from the actual job posting URL.
    This parses JSON-LD JobPosting schema natively generated by modern ATS systems 
    (Greenhouse, Workday, Lever, etc.) to get data independent of complex UI loads.
    If schema falls back, attempts heuristic HTML parsing.
    """
    try:
        # Dynamic delay so we aren't blocked when fetching hundreds of missing descriptions
        time.sleep(random.uniform(1.0, 2.5))
        resp = scraper.get(url, timeout=20)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 1. Look for Standard JSON-LD JobPosting Schema (Highly Reliable)
        schemas = soup.find_all('script', type='application/ld+json')
        for schema_tag in schemas:
            try:
                data = json.loads(schema_tag.string)
                # Some sites wrap multiple schemas in a list
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'JobPosting' and item.get('description'):
                            return clean_text(item['description'])
                elif data.get('@type') == 'JobPosting' and data.get('description'):
                    return clean_text(data['description'])
            except:
                continue

        # 2. Heuristic HTML Extraction Fallback
        for el in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'noscript']):
            el.decompose()

        target_classes = ['job-description', 'description', 'posting-desc', 'job-details', 'jobDetails', 'job-info', 'show-more-less-html__markup', 'app-job-description']
        target_ids = ['job-description', 'description', 'job-details', 'content']

        desc_container = None
        for class_name in target_classes:
            desc_container = soup.find(class_=re.compile(class_name, re.I))
            if desc_container: break

        if not desc_container:
            for id_name in target_ids:
                desc_container = soup.find(id=re.compile(id_name, re.I))
                if desc_container: break

        if desc_container:
            return clean_text(desc_container.get_text(separator=' ', strip=True))

        return ""
    except Exception as e:
        return ""

def get_relative_time(dt):
    """
    Returns a human-readable 'time ago' string.
    Specifically handles the client request: jobs within 24-48h show as '1 day ago'.
    """
    if not dt:
        return "—"
    
    from django.utils import timezone
    now = timezone.now()
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)
        
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    if seconds < 172800: # Up to 48 hours (Revised from 36h)
        return "1 day ago"
    
    # Fallback to date for very old ones (though they should be archived)
    return dt.strftime('%b %d, %Y')
