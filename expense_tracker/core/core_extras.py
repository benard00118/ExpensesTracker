from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    return value - arg

@register.filter
def div(value, arg):
    return value / arg if arg != 0 else 0

@register.filter
def mul(value, arg):
    return value * arg