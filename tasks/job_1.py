from celery_app.utils import create_celery
from core.config import get_settings

settings = get_settings()

celery = create_celery()


@celery.task(name="job_1", bind=True, max_retries=3, default_retry_delay=10, queue="user_github_que") #  ack_late=True, jesli chcemy od razu usuwac po odczytaniu wiadomosci z que
def job_1(self, **kwargs):
    print(f"job_1(que1): {kwargs}")


