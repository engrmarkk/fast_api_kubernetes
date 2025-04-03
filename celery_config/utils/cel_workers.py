from celery import Celery, shared_task
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime
import celery_config.schedule_config as celeryConfig
from jinja2 import Environment, FileSystemLoader
import traceback
from dotenv import load_dotenv
from logger import logger

load_dotenv()


def make_celery():
    celery = Celery(
        "wallet",
        backend=f"redis://{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}",
        broker=f"redis://{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}",
    )
    celery.conf.update(
        {
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],
            "timezone": "UTC",
            "enable_utc": True,
            "broker_connection_retry_on_startup": True,
        }
    )

    return celery


celery = make_celery()


@shared_task
def add_numbers(x, y):
    logger.info("Adding")
    return x + y


# @shared_task
# def send_mail(context):
#     try:
#         logger.info("Sending Mail")
#         smtp_host = "smtp.gmail.com"
#         smtp_port = 587
#         smtp_user = os.environ.get("EMAIL_USER")
#         smtp_password = os.environ.get("EMAIL_PASSWORD")
#
#         server = smtplib.SMTP(smtp_host, smtp_port)
#         server.starttls()
#         server.login(smtp_user, smtp_password)
#
#         from_email = "support@teamflow.com"
#         to_email = context["email"]
#         subject = context["subject"]
#
#         # Construct the path to the HTML file within the templates folder
#         template_path = os.path.join(os.getcwd(), "templates", context["template_name"])
#
#         # Read the HTML file content
#         with open(template_path, "r") as html_file:
#             body = html_file.read()
#
#         # send context inside the html file
#         body = render_template_string(body, **context)
#
#         msg = MIMEMultipart()
#         msg["From"] = from_email
#         msg["To"] = to_email
#         msg["Subject"] = subject
#
#         # Change the MIME type to 'html'
#         msg.attach(MIMEText(body, "html"))
#
#         server.sendmail(from_email, to_email, msg.as_string())
#
#         server.quit()
#         return "Mail sent successfully"
#
#     except Exception as e:
#         logger.exception("Failed to send mail from celery")
#         logger.error(f"{e}: error@celery/send_mail")
#         return "Failed to send mail"


# Create a Jinja2 Environment
templates_path = os.path.join(os.getcwd(), "templates")
jinja_env = Environment(loader=FileSystemLoader(templates_path))


@shared_task
def send_mail(context):
    try:
        logger.info("Sending Mail")
        smtp_host = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = os.environ.get("EMAIL_USER")
        smtp_password = os.environ.get("EMAIL_PASSWORD")

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        from_email = "support@teamflow.com"
        to_email = context["email"]
        subject = context["subject"]

        # Load the HTML template
        template = jinja_env.get_template(context["template_name"])

        # Render the template with the context
        body = template.render(**context)

        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        # Attach the rendered HTML content
        msg.attach(MIMEText(body, "html"))

        server.sendmail(from_email, to_email, msg.as_string())

        server.quit()
        return "Mail sent successfully"

    except Exception as e:
        logger.exception("Failed to send mail from celery")
        logger.error(f"{e}: error@celery/send_mail")
        return "Failed to send mail"


#
#
# @shared_task
# def send_all_users_email(users, uploaded_by, document_name, project_name):
#     try:
#         if users:
#             for user in users:
#                 payload = {
#                     "email": user["email"],
#                     "subject": "Document Uploaded",
#                     "template_name": "document_upload.html",
#                     "name": f"{user['last_name'].title()} {user['first_name'].title()}",
#                     "project_name": project_name,
#                     "document_name": document_name,
#                     "uploaded_by": uploaded_by,
#                     "date": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
#                 }
#                 send_mail.delay(payload)
#         return "Mail sent successfully"
#
#     except Exception as e:
#         logger.error(f"{e}: error@celery/send_all_users_email")
#         return "Failed to send mail"
