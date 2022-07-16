from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from .functions import get_option, get_advanced_option
from django.utils.html import strip_tags

def send_when_comment():
    conf = get_advanced_option("smtp")
    if conf == None:
        return False
    return conf.get("send_when_comment", True)

def send_when_reply():
    conf = get_advanced_option("smtp")
    if conf == None:
        return False
    return conf.get("send_when_reply", True)

def send(subject, html, to):
    conf = get_advanced_option("smtp", {})
    backend = EmailBackend(
        host = conf.get("host", ""),
        port = conf.get("port", 465),
        username = conf.get("user", ""),
        password = conf.get("password", ""),
        use_tls = conf.get("use_tls", False),
        use_ssl = conf.get("use_ssl", False),
        fail_silently = True,
    )
    body = strip_tags(html)
    email = EmailMultiAlternatives(
        subject = subject,
        body = body,
        from_email = conf.get("from", conf.get("user", "")),
        to = to,
        connection = backend,
    )
    email.attach_alternative(html, "text/html")
    email.send()

def send_comment_notification(post_title, url):
    send("New comment - " + get_option("site_name"),
        "Hi " + get_option("username") + ",<br /><br />" + \
        "There is a new comment on your article: <i>" + \
            post_title + "</i>.<br /><br />" + \
        "<a href=\"" + url + "\">Click here</a> to view.",
        [get_option("email")]
    )

def send_reply_notification(author, email, url):
    site_name = get_option("site_name")
    send("You have received a new reply - " + site_name,
        "Hi " + author + ",<br /><br />" + \
        "You have received a new reply to your comment on " + \
            site_name + ".<br /><br />" + \
        "<a href=\"" + url + "\">Click here</a> to view.",
        [email]
    )
