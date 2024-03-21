"""
Application HTML forms.
"""
from django import forms


class ScrapeRequestForm(forms.Form):
    """Admin-only form for requesting website scraping."""

    site_url = forms.URLField(max_length=64, min_length=4)