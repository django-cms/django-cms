from cms.plugins.text.models import Text
from django import forms
from django.forms.models import ModelForm
import html5lib
from html5lib import sanitizer


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
    # if the first element after <body> is a html tag, this returns an Element
    # instance, otherwise a (unicode) string, this is why we need to check
    # the output of this and potentially call .toxml() again.
    out = reduce(lambda x,y:x.toxml()+y.toxml(), body.childNodes)
    if isinstance(out, basestring):
        return out
    return out.toxml()

class TextForm(ModelForm):
    body = forms.CharField()
    
    class Meta:
        model = Text
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
    
    parser = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
    
    def clean_body(self):
        data = self.cleaned_data['body']
        doc = self.parser.parse(data)
        html = _get_inner_body(doc)
        return html
