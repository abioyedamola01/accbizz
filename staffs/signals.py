from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from .models import UserSession



@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    if not request.session.session_key:
        request.session.create()
        
    session_instance = Session.objects.get(session_key=request.session.session_key)
    
    UserSession.objects.get_or_create(user=user, session=session_instance)

