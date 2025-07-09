from django import template
from django.utils.safestring import mark_safe
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    if isinstance(field, BoundField):
        existing = field.field.widget.attrs.get('class', '')
        combined = f"{existing} {css_class}".strip()
        return field.as_widget(attrs={"class": combined})
    return field

@register.filter(name='add_placeholder')
def add_placeholder(field, text):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"placeholder": text})
    return field

@register.filter(name='set_autofocus')
def set_autofocus(field):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"autofocus": "autofocus"})
    return field

@register.filter(name='set_required')
def set_required(field, val=True):
    if isinstance(field, BoundField) and val:
        return field.as_widget(attrs={"required": "required"})
    return field


@register.filter(name='add_attr')
def add_attr(field, attrs):
    """
    Örnek kullanımlar:
      {{ field|add_attr:"required" }}
      {{ field|add_attr:"autofocus:autofocus,required:required,style:color:red" }}
    """
    if not isinstance(field, BoundField):
        return field

    widget_attrs = field.field.widget.attrs.copy()
    for pair in attrs.split(','):
        if ':' in pair:
            key, val = pair.split(':', 1)
        else:
            key = val = pair
        widget_attrs[key] = val

    return field.as_widget(attrs=widget_attrs)
@register.filter(name='label_with_icon')
def label_with_icon(field, icon):
    if isinstance(field, BoundField):
        label_html = field.label_tag(attrs={"style": "font-weight:bold;"})
        return mark_safe(f'{label_html} {icon}')
    return mark_safe(f'<label>{icon}</label>')
