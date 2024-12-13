=======================
Documentation Guide
=======================

This directory contains the documentation for django CMS. The documentation is written in reStructuredText (RST) format and built using Sphinx.

Building the documentation
-------------------------

1. Install documentation dependencies::

    pip install -e .[docs]
    # First install the enchant library:
    
    # On Ubuntu/Debian:
    sudo apt-get install enchant-2
    
    # On macOS:
    brew install enchant
    
    # On Windows:
    # Download from https://github.com/AbiWord/enchant/releases
    
    # Then install Python packages:
    pip install sphinx sphinxcontrib-spelling pyenchant rstcheck codespell

    # Note: If you get an error about missing 'enchant' library,
    # make sure you installed the system library above before
    # installing pyenchant

2. Build the documentation::

    cd docs/
    make html

The built documentation will be in ``docs/_build/html/``.

Spell checking
-------------

To check spelling::

    sphinx-build -b spelling docs/ docs/_build/spelling

Add technical terms and proper nouns to ``spelling_wordlist`` to whitelist them.

RST validation
-------------

To validate RST syntax::

    # Ignore common directive/role warnings:
    rstcheck --recursive --report-level warning docs/

Documentation Standards
---------------------

- Use sentence case for headings
- Keep line length to 119 characters
- Use double backticks for code/technical terms
- Include code examples for technical concepts
- Cross-reference related documentation
- Maintain consistent terminology
- Break complex topics into clear sections
- Include configuration examples
- Document version compatibility

Contributing
-----------

1. Check spelling and RST syntax
2. Follow documentation standards
3. Test code examples
4. Add cross-references
5. Submit pull request

For questions, join #documentation on `Discord <https://discord-docs-channel.django-cms.org>`_.
