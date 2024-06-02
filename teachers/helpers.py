from django.core.mail import send_mail

def send_forget_password_mail(email, token):
    subject = "Reset Your Password"
    message = f"Click the link below to reset your password:\n\nhttp://127.0.0.1:8000/parent/change_password/{token}"
    from_email = "crce.9539.ce@gmail.com"
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)