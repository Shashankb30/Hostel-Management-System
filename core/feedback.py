"""Show validation errors to the user the same way everywhere (Issue #13)."""
from django.contrib import messages


def flash_errors(request, error):
    """Add every message of a ValidationError to the page's alert area."""
    for text in error.messages:
        messages.error(request, text)
