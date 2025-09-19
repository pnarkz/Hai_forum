# forum/templatetags/forum_tags.py
from django import template
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from django.utils.html import format_html

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Form field'e CSS class ekler
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        attrs = field.field.widget.attrs.copy()
        existing_classes = attrs.get('class', '')
        if existing_classes:
            attrs['class'] = f"{existing_classes} {css_class}".strip()
        else:
            attrs['class'] = css_class
        field.field.widget.attrs.update(attrs)
    return field

@register.filter(name='add_attr')
def add_attr(field, attr_string):
    """
    Form field'e attribute ekler
    Kullanım: {{ field|add_attr:"rows:8,id:my_field" }}
    """
    if not hasattr(field, 'field') or not hasattr(field.field, 'widget'):
        return field
    
    try:
        # Birden fazla attribute desteği
        attributes = attr_string.split(',')
        for attr in attributes:
            if ':' in attr:
                key, value = attr.strip().split(':', 1)
                field.field.widget.attrs[key.strip()] = value.strip()
    except (ValueError, AttributeError):
        pass
    return field

@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder):
    """
    Form field'e placeholder ekler
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        field.field.widget.attrs['placeholder'] = placeholder
    return field

@register.filter(name='set_autofocus')
def set_autofocus(field):
    """
    Form field'e autofocus attribute ekler
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        field.field.widget.attrs['autofocus'] = 'autofocus'
    return field

@register.filter(name='set_required')
def set_required(field):
    """
    Form field'e required attribute ekler
    """
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        field.field.widget.attrs['required'] = 'required'
    return field

@register.filter
def label_with_icon(bound_field, icon):
    """
    Form field label'ını icon ile birlikte döndürür
    """
    if not hasattr(bound_field, 'label') or not hasattr(bound_field, 'id_for_label'):
        return ''
    
    label = bound_field.label or ''
    field_id = bound_field.id_for_label or ''
    
    return format_html(
        '<label for="{}" class="font-semibold text-sm text-gray-700 flex items-center gap-2">{} {}</label>',
        field_id,
        icon,
        label
    )