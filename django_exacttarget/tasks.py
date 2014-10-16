# -*- coding: utf-8 -*-
from celery import shared_task

from .service import ExactTargetService


@shared_task
def send_mail(recipients, email_message):
    return ExactTargetService.send_email(recipients, email_message)
