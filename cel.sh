#! /bin/bash

source env/bin/activate
celery -A celery_config.utils.cel_workers.celery worker --loglevel=info --concurrency=4 --autoscale=4,2 -E -B
