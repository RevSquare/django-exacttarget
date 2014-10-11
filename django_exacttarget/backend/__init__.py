import uuid
import threading

from FuelSDK import ET_Client
from FuelSDK.objects import ET_Email, ET_TriggeredSend, ET_Subscriber

from django.core.mail.backends.base import BaseEmailBackend
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


class EmailBackend(BaseEmailBackend):
    """ExactTarget email backend"""

    def __init__(self, *args, **kwargs):
        """Initializes backend ET_Client"""
        app_signature = getattr(settings, 'FUELSDK_APP_SIGNATURE', None)
        client_id = getattr(settings, 'FUELSDK_CLIENT_ID', None)
        client_secret = getattr(settings, 'FUELSDK_CLIENT_SECRET', None)
        self.send_classification_key = getattr(
            settings, 'FUELSDK_SEND_CLASSIFICATION_CONSUMER_KEY', None)

        if app_signature is None or client_id is None or \
                client_secret is None or self.send_classification_key is None:
            raise ImproperlyConfigured('Missing FuelSDK configuration')

        self._lock = threading.RLock()

        self.et_client = ET_Client(debug=settings.DEBUG, params={
            'appsignature': app_signature,
            'clientid': client_id,
            'clientsecret': client_secret
        })
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
        et_email = ET_Email()
        et_email.auth_stub = self.et_client
        message_uid = uuid.uuid4()
        et_email.props = {
            'CustomerKey': message_uid,
            'Name': message_uid,
            'Subject': email_message.subject,
            'TextBody': email_message.body
        }
        if hasattr(email_message, 'alternatives'):
            html_body = filter(
                lambda item: item[1] == 'text/html',
                email_message.alternatives)
            if html_body:
                et_email.props.update({
                    'HTMLBody': html_body[0][0]
                })
        email_response = et_email.post()

        send_trigger_uuid = uuid.uuid4()
        et_sendtrigger = ET_TriggeredSend()
        et_sendtrigger.auth_stub = self.et_client
        et_sendtrigger.props = {
            'CustomerKey': send_trigger_uuid,
            'Name': send_trigger_uuid,
            'Email': {
                'ID': str(email_response.results[0]['NewID']),
            },
            'SendClassification': {
                'CustomerKey': self.send_classification_key,
            }
        }
        et_sendtrigger.post()

        et_sendtrigger.props = {
            'CustomerKey': send_trigger_uuid,
            'TriggeredSendStatus': 'Active'
        }
        et_sendtrigger.patch()

        emails_to = email_message.to
        subscribers = []
        for email in emails_to:
            et_subscriber = ET_Subscriber()
            et_subscriber.auth_stub = self.et_client
            et_subscriber.props = ["SubscriberKey", "EmailAddress", "Status"]
            et_subscriber.search_filter = {
                'Property': 'SubscriberKey',
                'SimpleOperator': 'equals',
                'Value': email
            }
            get_response = et_subscriber.get()
            if get_response.code == 200 and len(get_response.results) == 0:
                et_subscriber.props = {
                    "SubscriberKey": email,
                    "EmailAddress": email
                }
            elif get_response.code == 200:
                subscriber = get_response.results[0]
                if not subscriber.Status != 'Active':
                    et_subscriber.props = {
                        "SubscriberKey": email,
                        "Status": "Active"
                    }
                    et_subscriber.patch()
            subscribers.append({
                'EmailAddress': email,
                'SubscriberKey': email
            })
        et_sendtrigger.subscribers = subscribers
        response = et_sendtrigger.send()
        if response.code != 200:
            if not self.fail_silently:
                raise
            return False
