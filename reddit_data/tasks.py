from celery import Celery
from reddit_data.scrape import Scraper
import os
import logging
import json


logging.basicConfig(filename='/data/reddit-data.log', level=logging.INFO)


celery_app = Celery(
    'tasks',
    broker=os.environ.get('CELERY_BROKER'),
    backend=os.environ.get('CELERY_BACKEND')
)
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def scrape_id(self, sid):
    Scraper().scrape(sid)


@celery_app.task(bind=True)
def scrape_id_pushshift(self, sid):
    try:
        Scraper().scrape_pushshift(sid)
    except json.JSONDecodeError:
        self.retry(countdown=5)
