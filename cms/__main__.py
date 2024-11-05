"""
Invokes djangocms when the cms module is run as a script.

Example: python -m cms mysite
"""
from cms.management import djangocms

if __name__ == "__main__":
    djangocms.execute_from_command_line()
