from firebase_admin import messaging
from app.models import User

def send_fcm_notification(user_id, title, message, data=None):
    try:
        user = User.objects.get(id=user_id)
        
        if not user.fcm_token:
            return False

        notification = messaging.Notification(
            title=title,
            body=message
        )
        print(user.fcm_token, ">>>>>>>>>>>>>>>")
        message = messaging.Message(
            notification=notification,
            token=user.fcm_token,
            data=data or {}
        )
        
        response = messaging.send(message)
        print("Successfully sent FCM notification:", response)
        return True
    
    except Exception as e:
        print("FCM Error:", str(e))
        return False