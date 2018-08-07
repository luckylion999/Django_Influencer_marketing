from django import template

register = template.Library()

@register.filter
def valid_username(value):
	if not value:
		return ''

	return value.replace("@","")