"""Frontend editing: the editor itself, generic over the edited model.

Frontend editing is a capability core provides *to* the other containers rather
than a layer each one repeats: a model becomes editable by registering in
``cms_config.py`` (``cms_toolbar_enabled_models``), exactly as a third-party app
does.

As a presentation layer this package may use the toolbar framework; core's
model, services and admin layers may not.
"""
