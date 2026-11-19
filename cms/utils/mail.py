from django.contrib.sites.models import Site
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from cms.utils.urlutils import admin_reverse, urljoin

MAIL_DELIVERY_ERRORS = (OSError,)
if hasattr(mail, "MailerDoesNotExist"):
    MAIL_DELIVERY_ERRORS += (mail.MailerDoesNotExist,)


def send_mail(subject, txt_template, to, context=None, html_template=None, fail_silently=True, site=None):
    """
    Render and send multipart mail. With ``fail_silently=True``, suppress
    transport errors and an unconfigured mailer, but not programming errors.
    """
    site = site or Site.objects.get_current()

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
    try:
        message.send()
    except MAIL_DELIVERY_ERRORS:
        if not fail_silently:
            raise


def mail_page_user_change(user, created=False, password="", site=None):
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
    }, 'admin/cms/mail/page_user_change.html', site=site)
