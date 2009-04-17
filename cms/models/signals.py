from django.dispatch import Signal

"""Signals provided by cms - maybe should be moved under models
"""
page_moved = Signal(providing_args=["instance"])
