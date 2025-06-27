from firebase_admin import messaging
from app.models import User

def send_order_status_notifications(order, new_status, updated_by_user):
    """Send notifications to relevant parties about order status changes."""
    try:
        data = {
            "order_id": str(order.id),
            "type": "order_status_update",
            "status": new_status
        }

        if order.user_id.fcm_token and str(order.user_id.id) != str(updated_by_user.id):
            send_fcm_notification(
                user_id=order.user_id.id,
                title=f"Order #{order.order_number} Updated",
                message=f"Your order #{order.order_number} is now {new_status}",
                data=data
            )
        
        if (order.seller_id and order.seller_id.user_id and 
            str(order.seller_id.user_id.id) != str(updated_by_user.id)):
            send_fcm_notification(
                user_id=order.seller_id.user_id.id,
                title=f"Order Update: #{order.order_number}",
                message=f"Order #{order.order_number} status changed to {new_status}",
                data=data
            )
        
        if not updated_by_user.is_admin:
            admin_users = User.objects(is_admin=True)
            for admin in admin_users:
                if admin.fcm_token and str(admin.id) != str(updated_by_user.id):
                    send_fcm_notification(
                        user_id=admin.id,
                        title="Order Status Update",
                        message=f"{updated_by_user.name} changed order #{order.order_number} to {new_status}",
                        data=data
                    )
    
    except Exception as e:
        print(f"Error sending order status notifications: {str(e)}")

def send_fcm_notification(user_id, title, message, data=None):
    try:
        user = User.objects.get(id=user_id)
        if not user.fcm_token:
            return False

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message
            ),
            token=user.fcm_token,
            data=data or {},
            android=messaging.AndroidConfig(priority='high'),
            apns=messaging.APNSConfig(headers={'apns-priority': '10'})
        )
        
        response = messaging.send(message)
        print(f"Sent notification to user {user_id}: {response}")
        return True

    except messaging.UnregisteredError:
        print(f"Removing invalid FCM token for user {user_id}")
        user.fcm_token = None
        user.save()
    except Exception as e:
        print(f"FCM Error for user {user_id}: {str(e)}")
    return False