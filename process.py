import logging
import time
import os

from reddit_data.scrape import Scraper
from reddit_data.queue import RedisQueue

logging.basicConfig(filename='/data/reddit-data.log', level=logging.INFO)


def main():
    queue = RedisQueue(
        'reddit-data',
        host=os.environ.get('REDIS_HOST'),
        port=os.environ.get('REDIS_PORT', 6379),
        password=os.environ.get('REDIS_PASSWORD')
    )

    queue_failed = RedisQueue(
        'reddit-data-failed',
        host=os.environ.get('REDIS_HOST'),
        port=os.environ.get('REDIS_PORT', 6379),
        password=os.environ.get('REDIS_PASSWORD')
    )

    scraper = Scraper()

    while True:

        if queue.empty():
            time.sleep(60)
        else:
            try:
                sid = queue.get(block=True).decode('utf-8')
                scraper.scrape(sid)
            except Exception as e:
                queue_failed.put(sid)
                logging.exception('Scraping failed')


if __name__ == '__main__':
    main()
