from .models import *
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging

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
    # check if firebase_admin is already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_FILE_PATH)
        firebase_admin.initialize_app(cred)
    #create array of push ids
    push_registrations = PushNotificationRegistration.objects.filter(
        user__in=users
    )
    push_ids = push_registrations.values_list('push_id', flat=True)
    for push_id in push_ids:
        apns_config = messaging.APNSConfig(
            headers={
                "apns-priority": "10",  # High priority for immediate delivery
                "apns-expiration": "3600",  # Expiration time in seconds
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.Alert(
                        title=title,
                        body=text,
                        subtitle=subtitle,
                    ),
                    thread_id=thread_id,
                    collapse_id=collapse_id,
                    category=category,
                    custom_data=extra_data,
                    content_available=silent,
                )
            )
        )
        message = messaging.Message(
            apns=apns_config,
            token=push_id,
        ) 
        try:
            response = messaging.send(message)
            print(f"Successfully sent message: {response} for push_id: {push_id}")
        except Exception as ex:
            print(f"Error sending message: {ex} for push_id: {push_id}")