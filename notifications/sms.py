import json
import ssl
import urllib.request
import urllib.parse

from django.conf import settings


def format_phone_number(phone_number):
    phone_number = str(phone_number).strip()

    if phone_number.startswith('0'):
        return '+254' + phone_number[1:]

    if phone_number.startswith('254'):
        return '+' + phone_number

    if phone_number.startswith('+254'):
        return phone_number

    return phone_number


def send_sms(phone_number, message):
    phone_number = format_phone_number(phone_number)

    url = 'https://api.sandbox.africastalking.com/version1/messaging'

    data = urllib.parse.urlencode({
        'username': settings.AFRICASTALKING_USERNAME,
        'to': phone_number,
        'message': message,
    }).encode('utf-8')

    request = urllib.request.Request(
        url,
        data=data,
        method='POST',
        headers={
            'apiKey': settings.AFRICASTALKING_API_KEY,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        },
    )

    ssl_context = ssl.create_default_context()

    with urllib.request.urlopen(
        request,
        context=ssl_context
    ) as response:
        return json.loads(
            response.read().decode('utf-8')
        )