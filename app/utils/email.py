import re

def is_valid_email(email):
    regex = r"[^@]+@[^@]+\.[^@]+"
    return re.match(regex, email)