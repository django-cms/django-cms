# -*- coding: utf-8 -*-
import html5lib
from html5lib import sanitizer


DEFAULT_PARSER = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)


def _get_inner_body(doc):
    # find 'body'
    def _rec(node):
        if node.type == 5: # Element Type
            if node.name == 'body': # the body element
                return node
        for child in node.childNodes:
            childfound = _rec(child)
            if childfound:
                return childfound
        return None
    body = _rec(doc)
    out = []
    for node in body.childNodes:
        out.append(node.toxml())
    return u''.join(out)

def clean_html(data, full=True, parser=DEFAULT_PARSER):
    """
    Cleans HTML from XSS vulnerabilities using html5lib
    
    If full is False, only the contents inside <body> will be returned (without
    the <body> tags).
    """
    doc = parser.parse(data)
    if full:
        return doc.toxml()
    else:
        return _get_inner_body(doc)
