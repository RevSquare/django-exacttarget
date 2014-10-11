##################
Django Exacttarget
##################

Manages the integration of Exacttarget email platform in a django project. It allows to use exacttarget as an email backend to send all the system emails and to manage newsletter setup.

*******
Install
*******

It is strongly recommanded to install this theme from GIT with PIP onto you project virtualenv.

Add this line to your requirements.txt file:

.. code-block::  shell-session

    -e git+https://github.com/RevSquare/django-exacttarget#egg=django-exacttarget

And run:

.. code-block::  shell-session

    pip install -r requirements.txt

*****
Setup
*****

Before starting, you will need a Brightcove API token in order to connect to brightcove: http://docs.brightcove.com/en/video-cloud/media/guides/managing-media-api-tokens.html

The first step is to add the app in your installed apps list in settings.py

.. code-block::  python

    INSTALLED_APPS = (
        ...
        'django-exacttarget'
        ...
    )

The you will need to declare the loaders you want to add in your settings.py file

.. code-block::  python

    EMAIL_BACKEND = 'django_exacttarget.backend.EmailBackend'
    FUELSDK_APP_SIGNATURE = YOUR_EXACTTARGET_APP_SIGNATURE
    FUELSDK_CLIENT_ID = YOUR_EXACTTARGET_CLIENT_ID
    FUELSDK_CLIENT_SECRET = YOUR_EXACTTARGET_CLIENT_SECRET
    FUELSDK_SEND_CLASSIFICATION_CONSUMER_KEY = YOUR_EXACTTARGET_SEND_CLASSIFICATION_CONSUMER_KEY
