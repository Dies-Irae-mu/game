from django import template
from django.utils.safestring import mark_safe
import markdown2
import re

register = template.Library()

@register.filter
def markdownify(text):
    """Convert markdown to HTML"""
    if not text:
        return ''
    return mark_safe(markdown2.markdown(text))

@register.filter
def get(dictionary, key):
    """Get a value from a dictionary by key"""
    if not dictionary:
        return None
    return dictionary.get(key)

@register.filter
def replace(value, arg):
    """Replace all occurrences of the first argument with the second argument"""
    if not value or not arg:
        return value
    
    args = arg.split(',')
    if len(args) != 2:
        return value
    
    return value.replace(args[0], args[1]) 