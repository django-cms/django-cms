"""Core models: placeholders, plugins, and the user's clipboard.

These stay in the ``cms`` app -- a model's ``app_label`` follows the Django app
that contains its module, not the module's own path, so moving the file changes
neither the label nor the table (§4 of the refactor RFC).
"""
