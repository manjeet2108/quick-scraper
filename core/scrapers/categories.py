# core/scrapers/categories.py

JOB_CATEGORIES = {
    "Software Engineering": [
        "Software Engineer", "Software Developer", "Backend Developer", "Full Stack Developer",
        "Frontend Developer", "Platform Engineer", "Systems Engineer", "Java Backend Developer",
        "Java Developer", "iOS Developer", "Android Developer", "React Native Developer",
        "Blockchain Developer", "Graphics Engineer", "SAP Developer", ".NET Developer",
        "Embedded Systems Engineer", "Power Platform Developer"
    ],
    "Infrastructure & DevOps": [
        "Cloud Engineer", "DevOps Engineer", "Cloud Developer", "Site Reliability Engineer",
        "Security Engineer", "Network Engineer", "Systems Administrator", "AWS Java Developer",
        "AWS Azure", "AWS DevOps Engineer"
    ],
    "Data & AI": [
        "Data Analyst", "Data Engineer", "Data Science", "Machine Learning Engineer",
        "AI Engineer", "Gen AI", "Analytics Engineer", "Business Intelligence Analyst",
        "ETL Developer", "SQL Developer"
    ],
    "Security": [
        "Security Engineer", "Cybersecurity Analyst", "Security Analyst", 
        "Application Security Engineer", "Network Security Engineer", "Information Security Analyst"
    ],
    "Quality & Testing": [
        "QA Engineer", "Test Engineer", "Automation Test Engineer", "QA Analyst", "SDET", 
        "Quality Engineer", "Quality Control"
    ],
    "Management": [
        "Product Manager", "Engineering Manager", "Project Manager", "Program Manager",
        "Supply Chain Manager", "Finance Manager", "Product Owner", "Marketing Manager"
    ],
    "Design": [
        "UI Designer", "UX Designer", "Product Designer", "UI UX Designer"
    ],
    "Support & IT": [
        "IT Support Engineer", "Technical Support Engineer", "Salesforce Administrator",
        "Technical Support"
    ],
    "Specialized": [
        "SAP", "Salesforce Developer", "Business Analyst", "Supply Chain", 
        "Marketing Analyst", "Aerospace Engineer", "Mechanical Engineer", 
        "Civil Engineer", "Physical Therapist", "Finance Analyst", "Risk Analyst", 
        "Product Analyst", "Clinical Research Scientist", "Drug Safety Associate",
        "Construction Engineer"
    ]
}

def get_all_titles():
    """Returns a flat list of all relevant job titles for filtering."""
    titles = []
    for cat in JOB_CATEGORIES.values():
        titles.extend(cat)
    return titles

def matches_target_titles(title):
    """
    Check if a job title matches any of the target categories.
    Uses fuzzy matching (substring) for better coverage.
    """
    if not title:
        return False
    
    title_lower = title.lower()
    all_titles = get_all_titles()
    
    for target in all_titles:
        target_lower = target.lower()
        # Direct match or target is a significant part of the title
        if target_lower in title_lower:
            # Avoid too broad matches (e.g., "SAP" shouldn't match "Disappearing")
            if len(target_lower) > 3 or f" {target_lower} " in f" {title_lower} ":
                return True
                
    return False

