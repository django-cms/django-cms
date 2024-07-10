from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from cms.utils.urlutils import admin_reverse, urljoin


def send_mail(subject, txt_template, to, context=None, html_template=None, fail_silently=True):
    """
    Multipart message helper with template rendering.
    """
    site = Site.objects.get_current()

    context = context or {}
    context.update({
        'login_url': "https://%s" % urljoin(site.domain, admin_reverse('index')),
        'title': subject,
    })

    txt_body = render_to_string(txt_template, context)

    message = EmailMultiAlternatives(subject=subject, body=txt_body, to=to)

    if html_template:
        body = render_to_string(html_template, context)
        message.attach_alternative(body, 'text/html')
    message.send(fail_silently=fail_silently)


def mail_page_user_change(user, created=False, password=""):
    """
    Send email notification to given user.
    Used it PageUser profile creation/update.
    """
    if created:
        subject = _('CMS - your user account was created.')
    else:
        subject = _('CMS - your user account was changed.')
    send_mail(subject, 'admin/cms/mail/page_user_change.txt', [user.email], {
        'user': user,
        'password': password or "*" * 8,
        'created': created,
    }, 'admin/cms/mail/page_user_change.html')
