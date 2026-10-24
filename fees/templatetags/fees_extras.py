from django import template

from fees.services import money as format_money

register = template.Library()


@register.filter
def money(value):
    """{{ 50000|money }} -> Rs. 50,000"""
    return format_money(value)
