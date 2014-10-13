import uuid
import threading

from django.core.mail.backends.base import BaseEmailBackend
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from ..service import ExactTargetService
try:
    from ..task import email_message as celery_send_email_message
except:
    celery_send_email_message = None


class EmailBackend(BaseEmailBackend):
    """ExactTarget email backend"""

    def __init__(self, *args, **kwargs):
        self._lock = threading.RLock()
        super(EmailBackend, self).__init__(*args, **kwargs)

    def send_messages(self, email_messages):
        """Sends one or more email messages"""
        if not email_messages:
            return False

        sent_counter = 0
        with self._lock:
            for message in email_messages:
                sent_flag = self._send(message)
                if sent_flag:
                    sent_counter += 1

        return sent_counter

    def _send(self, email_message):
        """Sends email message"""
        if celery_send_email_message:
            celery_send_email_message.delay(email_message)
        else:
            return ExactTargetService.send_email(
                email_message.recipients(), email_message)
