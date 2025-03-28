from django import template
import re

register = template.Library()

@register.filter
def display_username(user):
    """
    Filter to display only the username without the account number.
    Example: 'Scylla(account 5)' becomes 'Scylla'
    """
    if not user:
        return "Unknown"
    
    # Try to extract just the username from the string representation
    match = re.match(r'^([^(]+)', str(user))
    if match:
        return match.group(1).strip()
    return str(user) 