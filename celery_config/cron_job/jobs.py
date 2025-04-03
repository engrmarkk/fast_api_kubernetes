# from celery_config.utils.cel_workers import celery, shared_task, send_mail
# from models import Tasks
# from datetime import datetime
# from sqlalchemy import or_
#
#
# @shared_task
# def check_pending_tasks():
#     print("Checking Pending Tasks")
#     tasks = Tasks.query.filter(
#         or_(Tasks.status == "To Do", Tasks.status == "In Progress")
#     ).all()
#     for task in tasks:
#         # check if task is 7 days or less to due date
#         if 7 >= (task.due_date - datetime.now()).days >= 0:
#             print("I got a record")
#             date_left = (task.due_date - datetime.now()).days
#             will_expire_today = True if date_left == 0 else False
#             date_left_w = "day" if date_left == 1 else "days"
#             payload = {
#                 "email": task.assignee.email,
#                 "subject": "Pending Task",
#                 "template_name": "pending.html",
#                 "name": f"{task.assignee.last_name.title()} {task.assignee.first_name.title()}",
#                 "task": task.title.title(),
#                 "due_date": task.due_date.strftime("%d-%b-%Y"),
#                 "project_name": task.project.name.title(),
#                 "status": task.status,
#                 "date_left": date_left,
#                 "date_left_w": date_left_w,
#                 "will_expire_today": will_expire_today,
#                 "date": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
#             }
#             print("Sending mail")
#             send_mail.delay(payload)
#
#     return True
#
#
# # update task to expired if the due date has passed
# @shared_task
# def update_expired_tasks():
#     print("Updating Expired Tasks")
#
#     # Filter tasks once, then check expiration in the loop
#     tasks = Tasks.query.filter(
#         or_(Tasks.status == "To Do", Tasks.status == "In Progress"),
#         Tasks.due_date < datetime.now(),
#     ).all()
#
#     for task in tasks:
#         task.status = "Expired"
#         task.update()
#
#         # Prepare payload outside the loop if the same across tasks
#         payload = {
#             "email": task.assignee.email,
#             "subject": "Expired Task",
#             "template_name": "expired.html",
#             "name": f"{task.assignee.last_name.title()} {task.assignee.first_name.title()}",
#             "task": task.title.title(),
#             "due_date": task.due_date.strftime("%d-%b-%Y"),
#             "project_name": task.project.name.title(),
#             "status": task.status,
#             "date": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
#         }
#         send_mail.delay(payload)
#
#     return True
