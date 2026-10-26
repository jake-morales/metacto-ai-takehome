import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="markdown")
def markdown_filter(value):
    extensions = ["fenced_code", "tables", "nl2br"]
    return mark_safe(md.markdown(value or "", extensions=extensions))
