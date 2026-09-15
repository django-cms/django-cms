"""The placeholder/plugin core container.

Everything here is about placeholders and plugins and nothing here knows that
pages exist. Other containers become editable by registering in their
``cms_config.py``; core never imports them.
"""
