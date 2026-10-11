from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_contact_message(site_info, name, email, message, phone=None, service=None):
    context = {
        'name': name,
        'email': email,
        'phone': phone if phone else None,
        'service': service if service else None,
        'message': message,
    }
    
    
    html_message = render_to_string("messages/contact_message.html", context)
    
    plain_message = (
        f"New Customer Enquiry\n\n"
        f"Customer Name: {name}\n"
        f"Email Address: {email}\n"
    )
    if phone:
        plain_message += f"Phone Number: {phone}\n"
        
    enquiry_type = service if service else "General Enquiry"
    plain_message += f"Enquiry Type: {enquiry_type}\n\n"
    plain_message += f"Message:\n{message}"


    print(plain_message)
    print(html_message)
    
    
    send_mail(
        subject = f"{site_info.display_name.capitalize()} · New Enquiry from {name}",
        message = plain_message,
        from_email = None,
        recipient_list = [f"{site_info.email}"],
        html_message = html_message,
        fail_silently = False,
    )
