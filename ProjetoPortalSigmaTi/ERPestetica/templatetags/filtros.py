from django import template
register = template.Library()

@register.filter
def replace(value, args):
    antigo, novo = args.split('|', 1)
    return value.replace(antigo, novo)
