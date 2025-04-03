# from celery.schedules import crontab
#
#
# CELERY_IMPORTS = ("celery_config.cron_job.jobs",)
# CELERY_TASK_RESULT_EXPIRES = 30
# CELERY_TIMEZONE = "UTC"
#
# CELERY_ACCEPT_CONTENT = ["json", "msgpack", "yaml"]
# CELERY_TASK_SERIALIZER = "json"
# CELERY_RESULT_SERIALIZER = "json"
#
# CELERYBEAT_SCHEDULE = {
#     "check_task": {
#         "task": "celery_config.cron_job.jobs.check_pending_tasks",
#         "schedule": crontab(minute=28, hour=20),
#     },
#     "update_expired_task": {
#         "task": "celery_config.cron_job.jobs.update_expired_tasks",
#         "schedule": crontab(minute=30, hour=00),
#     },
# }
