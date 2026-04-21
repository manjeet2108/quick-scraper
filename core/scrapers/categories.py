# core/scrapers/categories.py

JOB_CATEGORIES = {
    "1. Software & Technology": [
        "Software Engineer", "Software Developer", "Backend Developer", "Frontend Developer",
        "Full Stack Developer", "Web Developer", "Mobile Developer", "iOS Developer",
        "Android Developer", "Game Developer", "DevOps Engineer", "Site Reliability Engineer",
        "Cloud Engineer", "Platform Engineer", "Systems Engineer", "Embedded Systems Engineer",
        "Firmware Engineer", "Application Developer", "Technical Lead", "Engineering Manager",
        "Chief Technology Officer"
    ],
    "2. Data & AI": [
        "Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer",
        "AI Engineer", "Deep Learning Engineer", "NLP Engineer", "Computer Vision Engineer",
        "Analytics Engineer", "Business Intelligence Analyst", "BI Developer", "Data Architect",
        "Data Governance Specialist", "MLOps Engineer", "Research Scientist AI"
    ],
    "3. Cybersecurity": [
        "Cybersecurity Analyst", "Security Engineer", "Security Architect", "Penetration Tester",
        "Ethical Hacker", "Information Security Analyst", "Security Operations Analyst",
        "SOC Analyst", "Cloud Security Engineer", "Application Security Engineer", "CISO"
    ],
    "4. Product & Project Management": [
        "Product Manager", "Senior Product Manager", "Product Owner", "Product Analyst",
        "Technical Product Manager", "Program Manager", "Project Manager",
        "Technical Program Manager", "Scrum Master", "Agile Coach", "Delivery Manager"
    ],
    "5. Design & Creative": [
        "UX Designer", "UI Designer", "Product Designer", "Graphic Designer",
        "Motion Designer", "Visual Designer", "Interaction Designer", "Web Designer",
        "Creative Director", "Art Director", "Animator", "Game Designer"
    ],
    "6. Marketing": [
        "Marketing Manager", "Digital Marketing Manager", "Growth Marketer", "SEO Specialist",
        "SEM Specialist", "Content Marketing Manager", "Social Media Manager", "Brand Manager",
        "Marketing Analyst", "Performance Marketing Manager", "Marketing Operations Manager"
    ],
    "7. Sales": [
        "Sales Representative", "Account Executive", "Account Manager", "Sales Manager",
        "Regional Sales Manager", "Business Development Representative", "Sales Development Representative",
        "Enterprise Sales Executive", "Customer Success Manager", "Partnerships Manager", "Chief Revenue Officer"
    ],
    "8. Finance": [
        "Financial Analyst", "Accountant", "Senior Accountant", "Tax Consultant",
        "Auditor", "Investment Banker", "Portfolio Manager", "Risk Analyst",
        "Treasury Analyst", "Finance Manager", "CFO"
    ],
    "9. Human Resources": [
        "HR Generalist", "HR Manager", "Talent Acquisition Specialist", "Technical Recruiter",
        "HR Business Partner", "People Operations Manager", "Compensation Analyst",
        "Learning & Development Manager", "HR Director", "Chief Human Resources Officer"
    ],
    "10. Operations": [
        "Operations Manager", "Business Operations Analyst", "Supply Chain Manager",
        "Logistics Coordinator", "Procurement Specialist", "Vendor Manager",
        "Operations Analyst", "Plant Manager", "COO"
    ],
    "11. Healthcare": [
        "Doctor", "Physician", "Surgeon", "Nurse", "Nurse Practitioner", "Pharmacist",
        "Medical Assistant", "Radiologist", "Lab Technician", "Physical Therapist",
        "Healthcare Administrator"
    ],
    "12. Legal": [
        "Lawyer", "Attorney", "Legal Counsel", "Corporate Counsel", "Legal Analyst",
        "Paralegal", "Compliance Officer", "Contract Manager", "Legal Operations Manager"
    ],
    "13. Education": [
        "Teacher", "Lecturer", "Professor", "Teaching Assistant", "Instructional Designer",
        "Academic Advisor", "School Counselor", "Principal", "Education Consultant"
    ],
    "14. Customer Support": [
        "Customer Support Representative", "Customer Success Manager", "Technical Support Engineer",
        "Help Desk Technician", "Support Specialist", "Call Center Agent"
    ],
    "15. Business & Strategy": [
        "Business Analyst", "Strategy Analyst", "Management Consultant", "Business Consultant",
        "Corporate Strategy Manager", "Operations Consultant"
    ],
    "16. Engineering Non-Software": [
        "Mechanical Engineer", "Electrical Engineer", "Civil Engineer", "Chemical Engineer",
        "Industrial Engineer", "Manufacturing Engineer", "Aerospace Engineer"
    ]
}

def get_all_titles():
    titles = []
    for cat in JOB_CATEGORIES.values():
        titles.extend(cat)
    return titles
