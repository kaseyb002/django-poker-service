from .models import *
import requests
import json
from django.conf import settings

def send_push(to_user, 
              text, 
              title=None, 
              subtitle=None, 
              category=None, 
              extra_data=None, 
              silent=False):
    send_push_to_users(
        users=(to_user,), 
        text=text, 
        title=title, 
        subtitle=subtitle, 
        category=category, 
        extra_data=extra_data,
        silent=silent
    )

def get_user_push_id(user):
    return user.account.push_id

def send_push_to_users(
    users,
    text,
    title=None,
    subtitle=None,
    category=None,
    extra_data=None,
    silent=False
):
    if not users:
        return
    #create array of push ids
    push_registrations = PushNotificationRegistration.objects.filter(
        user__in=users
    )
    push_ids = push_registrations.values_list('push_id', flat=True)
    print(list(push_ids))
    #start creating payload
    data = {
        'include_player_ids': list(push_ids),
        'contents': {"en": text},
        #'app_id': settings.ONE_SIGNAL_APP_ID}
    }
    if title:
        data['headings'] = {"en": title}
    if subtitle:
        data['subtitle'] = {"en": subtitle}
    if category:
        data['ios_category'] = category
    if extra_data:
        data['data'] = extra_data
    if silent:
        data['ios_sound'] = 'nil'
    else:
        data['ios_sound'] = 'hhl.m4a'
    try:
        # headers = {'Content-Type': 'application/json',
        #           'Authorization': 'Basic ' + settings.ONE_SIGNAL_REST_KEY,}
        print(data)
        # requests.post(ONE_SIGNAL_CREATE_NOTIFICATION_URL, data=json.dumps(data), headers=headers)
    except Exception as ex:
        print(ex)