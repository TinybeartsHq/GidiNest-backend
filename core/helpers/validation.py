import re

def is_official_email(email):
    # List of known free email domains
    free_domains = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
        "icloud.com", "mail.com", "zoho.com", "yandex.com", "protonmail.com"
    ]
    
    # Regular expression for validating an email address
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    # Check if the email address is valid
    if not email_regex.match(email):
        return False
    
    # Extract the domain part of the email
    domain = email.split('@')[-1]
    
    # Check if the domain is in the list of free email domains
    if domain in free_domains:
        return False
    
    return True