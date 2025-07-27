# forum/templatetags/forum_tags.py
from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    attrs = field.field.widget.attrs
    existing = attrs.get('class', '')
    attrs['class'] = (existing + ' ' + css_class).strip()
    return field

@register.filter(name='add_attr')
def add_attr(field, attr):
    """
    Kullanım: {{ field|add_attr:"rows:4" }}
    """
    try:
        name, val = attr.split(':', 1)
        field.field.widget.attrs[name] = val
    except ValueError:
        pass
    return field

@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder):
    field.field.widget.attrs['placeholder'] = placeholder
    return field

@register.filter(name='set_required')
def set_required(field):
    field.field.widget.attrs['required'] = 'required'
    return field
@register.filter(name='set_autofocus')
def set_autofocus(field):
    """
    Autocomplete and autofocus attribute ekler.
    Kullanım: {{ field|set_autofocus }}
    """
    field.field.widget.attrs['autofocus'] = 'autofocus'
    return field