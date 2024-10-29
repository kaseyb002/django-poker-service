from .models import *
import requests
import json
from django.conf import settings

def send_push(
    to_user, 
    text, 
    title=None, 
    subtitle=None, 
    category=None, 
    extra_data=None, 
    silent=False,
    thread_id=None,
    collapse_id=None,
):
    send_push_to_users(
        users=(to_user,), 
        text=text, 
        title=title, 
        subtitle=subtitle, 
        category=category, 
        extra_data=extra_data,
        silent=silent,
        thread_id=thread_id,
        collapse_id=collapse_id,
    )

def send_push_to_users(
    users,
    text,
    title=None,
    subtitle=None,
    category=None,
    extra_data=None,
    silent=False,
    thread_id=None,
    collapse_id=None,
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
    for push_id in push_ids:
        data = {
            'token': push_id,
        }
        data['apns'] = {}
        data['apns']['payload'] = {}
        data['apns']['payload']['aps'] = {}
        data['apns']['payload']['aps']['alert'] = {}
        data['apns']['payload']['aps']['alert']['body'] = text
        if title:
            data['apns']['payload']['aps']['alert']['title'] = title
        if subtitle:
            data['apns']['payload']['aps']['alert']['subtitle'] = subtitle
        if category:
            data['apns']['payload']['aps']['category'] = category
        if thread_id:
            data['apns']['payload']['aps']['thread-id'] = thread_id
        if collapse_id:
            data['apns']['payload']['aps']['collapse-id'] = collapse_id
        if silent:
            data['apns']['payload']['aps']['content-available'] = extra_data
        if extra_data:
            data['apns']['payload']['custom-data'] = extra_data
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + get_access_token(),
            }
            print(headers)
            url = "https://content-fcm.googleapis.com/v1/projects/" + str(settings.FIREBASE_SENDER_ID) + "/messages:send"
            something = requests.post(url, data=json.dumps(data), headers=headers)
            print(something.json())
        except Exception as ex:
            print(ex)


def get_access_token():
    return "fake"
"""
    credentials = service_account.Credentials.from_service_account_file(
        'service-account.json', scopes=SCOPES)
  request = google.auth.transport.requests.Request()
  credentials.refresh(request)
  return credentials.token
"""            
