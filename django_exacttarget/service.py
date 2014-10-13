# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from FuelSDK import ET_Client
from FuelSDK.objects import ET_Email, ET_TriggeredSend, ET_Subscriber


class ExactTargetService(object):
    @classmethod
    def get_client(cls):
        app_signature = getattr(settings, 'FUELSDK_APP_SIGNATURE', None)
        client_id = getattr(settings, 'FUELSDK_CLIENT_ID', None)
        client_secret = getattr(settings, 'FUELSDK_CLIENT_SECRET', None)

        if app_signature is None or client_id is None or \
                client_secret is None:
            raise ImproperlyConfigured('Missing FuelSDK configuration')

        return ET_Client(debug=settings.DEBUG, params={
            'appsignature': app_signature,
            'clientid': client_id,
            'clientsecret': client_secret
        })

    @classmethod
    def get_or_create_subscriber(cls, email):
        et_client = cls.get_client()
        et_subscriber = ET_Subscriber()
        et_subscriber.auth_stub = et_client
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
        return {
            'EmailAddress': email,
            'SubscriberKey': email
        }

    @classmethod
    def create_email_obj(cls, et_client, message):
        et_email = ET_Email()
        et_email.auth_stub = et_client
        message_uid = uuid.uuid4()
        et_email.props = {
            'CustomerKey': message_uid,
            'Name': message_uid,
            'Subject': message.subject,
            'TextBody': message.body
        }
        if hasattr(message, 'alternatives'):
            html_body = filter(
                lambda item: item[1] == 'text/html',
                message.alternatives)
            if html_body:
                et_email.props.update({
                    'HTMLBody': html_body[0][0]
                })
        return et_email.post()

    @classmethod
    def send_email(cls, recipients, message=None, email_id=None, context=None,
                   fail_silently=True):
        """
        @param recipients: emails list
        @param message: django EmailMessage instance
        @param email_id: Email ID in Exact Target
        @param context: dict with the variables to exact target Email object
        """
        if not message and not email_id:
            raise AttributeError(
                'You must give message or email key parameter')

        send_classification_key = getattr(
            settings, 'FUELSDK_SEND_CLASSIFICATION_CONSUMER_KEY', None)
        if send_classification_key is None:
            raise ImproperlyConfigured(
                'Missing CLASSIFICATION_CONSUMER_KEY configuration')
        et_client = cls.get_client()

        if not email_id:
            email_response = cls.create_email_obj(et_client, message)
            email_id = str(email_response.results[0]['NewID'])

        send_trigger_uuid = uuid.uuid4()
        et_sendtrigger = ET_TriggeredSend()
        et_sendtrigger.auth_stub = et_client
        et_sendtrigger.props = {
            'CustomerKey': send_trigger_uuid,
            'Name': send_trigger_uuid,
            'SendClassification': {
                'CustomerKey': send_classification_key,
            },
            'Email': {
                'ID': email_id,
            }
        }
        et_sendtrigger.post()

        et_sendtrigger.props = {
            'CustomerKey': send_trigger_uuid,
            'TriggeredSendStatus': 'Active'
        }
        et_sendtrigger.patch()

        subscribers = []
        for email in recipients:
            subscribers.append(cls.get_or_create_subscriber(email))
        et_sendtrigger.subscribers = subscribers
        response = et_sendtrigger.send()
        if response.code != 200:
            if not fail_silently:
                raise
            return False
        return True
