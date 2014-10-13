# -*- coding: utf-8 -*-
from celery import shared_task

from .service import ExactTargetService


@shared_task
def send_mail(email_message):
    ExactTargetService.send_email(email_message.recipients(), email_message)
