from kombu import Queue
from kombu.utils.url import safequote
from core.config import get_settings as app_settings

settings = app_settings()


class BaseSettings:
    """ here I configure celery_app"""

    aws_access_key_id = safequote("AKIA36DFXFF34UAZVBMY")
    aws_secret_access_key = safequote("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")

    broker_url = "sqs://{aws_access_key}:{aws_secret_key}@".format(
        aws_access_key=aws_access_key_id, aws_secret_key=aws_secret_access_key,
    )
    result_backend = "redis://localhost:6379/0"
    broker_transport = "sqs"
    task_default_queue = "default"
    task_queues = {
        Queue("user_github_que"),
        Queue("user_github_que2")
    }

    broker_transport_options = {
        'region': 'eu-north-1',
    }

    # worker_concurency = 5  # jesli nie ustawie to bierze tyle ile mam procesorow albo rdzeni

    include: list = ['tasks']


def get_settings():
    return BaseSettings()
