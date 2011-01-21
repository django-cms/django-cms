# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from cms.utils.urlutils import urljoin
from django.contrib import admin

def send_mail(subject, txt_template, to, context=None, html_template=None, fail_silently=True):
    """Multipart message helper with template rendering.
    """
    site = Site.objects.get_current()
    
    context = context or {}
    context.update({
        'login_url': "http://%s" % urljoin(site.domain, admin.site.root_path),
        'title': subject,
    })
    
    txt_body = render_to_string(txt_template, context)
    
    message = EmailMultiAlternatives(subject=subject, body=txt_body, to=to)
    
    if html_template:
        body = render_to_string(html_template, context)
        message.attach_alternative(body, 'text/html')
    message.send(fail_silently=fail_silently)