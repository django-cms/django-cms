"""The pages container: Page, PageContent, the page tree, URLs and apphooks.

Pages is a *client* of the core container's frontend editor rather than a
special case inside it: ``cms_config.py`` registers ``PageContent`` as editable,
the same door a third-party app uses.
"""
