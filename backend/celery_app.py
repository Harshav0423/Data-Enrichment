import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

app = Celery('backend')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks(lambda: ['apps.rest'])

# Queue Configuration
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'batch_processing': {
        'exchange': 'batch_processing',
        'routing_key': 'batch_processing',
    },
}

# Task Routing - Route specific tasks to specific queues
app.conf.task_routes = {
    # Parent task - orchestration (low volume, fast)
    'apps.rest.tasks.process_csv_create_batch': {
        'queue': 'default',
        'routing_key': 'default',
    },
    # Batch processing tasks - high volume, parallel execution
    'apps.rest.tasks.process_contact_batch_data': {
        'queue': 'batch_processing',
        'routing_key': 'batch_processing',
    },
    # Aggregation task - final step (low volume)
    'apps.rest.tasks.aggregate_batch_results': {
        'queue': 'default',
        'routing_key': 'default',
    },
}

# Default queue for any unrouted tasks
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'
