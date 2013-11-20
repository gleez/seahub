# encoding: utf-8
import logging
import string

from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse

from seahub.notifications.models import UserNotification
import seahub.settings as settings

# Get an instance of a logger
logger = logging.getLogger(__name__)

email_templates = (u'''Hi, ${to_user}
You've got ${count} new notice on ${site_name}.

Go check out at ${url}
''',
u'''Hi, ${to_user}
You've got ${count} new notices on ${site_name}.

Go check out at ${url}
''')

                  

site_name = settings.SITE_NAME
subjects = (u'New notice on %s' % site_name, u'New notices on %s' % site_name)
url = settings.SITE_BASE.rstrip('/') + reverse('user_notification_list')

class Command(BaseCommand):
    args = '<interval_seconds>'
    help = 'Send Email notifications to user if he/she has a unread notices every period of seconds .'

    def handle(self, *args, **options):
        logger.debug('Start sending user message...')
        try:
            interval_s = int(args[0])
        except (ValueError, IndexError) as e:
            raise CommandError('Please run command as: ./manage.py send_notices <interval_seconds>')
        
        self.do_action(interval_s)
        logger.debug('Finish sending user message.\n')

    def do_action(self, interval_s):
        unseen_notices = UserNotification.objects.get_all_notifications(
            seen=False, time_delta=interval_s)

        email_ctx = {}
        for notice in unseen_notices:
            if email_ctx.has_key(notice.to_user):
                email_ctx[notice.to_user] += 1
            else:
                email_ctx[notice.to_user] = 1
        
        for to_user, count in email_ctx.items():
            subject = subjects[1] if count > 1 else subjects[0]
            template = string.Template(email_templates[1]) if count > 1 else \
                string.Template(email_templates[0])
            content = template.substitute(to_user=to_user, count=count,
                                         site_name=site_name, url=url)

            try:
                send_mail(subject, content, settings.DEFAULT_FROM_EMAIL,
                          [to_user], fail_silently=False)
                logger.info('Successfully sent email to %s' % to_user)
            except Exception, e:
                logger.error('Failed to send email to %s, error detail: %s' % (to_user, e))

