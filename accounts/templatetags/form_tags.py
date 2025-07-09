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
def add_attr(field, args):
    """
    Kullanım: {{ field|add_attr:"key1:value1,key2:value2" }}
    Örneğin: {{ form.username|add_attr:"autofocus:autofocus,required:required" }}
    """
    if not isinstance(field, BoundField):
        return field

    attr_dict = {}
    for item in args.split(','):
        if ':' in item:
            key, val = item.split(':', 1)
        else:
            key, val = item, item
        attr_dict[key.strip()] = val.strip()
    # Mevcut widget attrs ile birleştir
    existing_attrs = field.field.widget.attrs.copy()
    existing_attrs.update(attr_dict)
    return field.as_widget(attrs=existing_attrs)

@register.filter(name='label_with_icon')
def label_with_icon(field, icon):
    if isinstance(field, BoundField):
        label_html = field.label_tag(attrs={"style": "font-weight:bold;"})
        return mark_safe(f'{label_html} {icon}')
    return mark_safe(f'<label>{icon}</label>')
