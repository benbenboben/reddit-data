
from peewee import *
from playhouse.pool import PooledPostgresqlExtDatabase
import datetime
import os

import threading
from peewee import Metadata


class ThreadSafeDatabaseMetadata(Metadata):
    def __init__(self, *args, **kwargs):
        # database attribute is stored in a thread-local.
        self._local = threading.local()
        super(ThreadSafeDatabaseMetadata, self).__init__(*args, **kwargs)

    def _get_db(self):
        return getattr(self._local, 'database', self._database)

    def _set_db(self, db):
        self._local.database = self._database = db

    database = property(_get_db, _set_db)


def get_db():
    try:
        db = SqliteDatabase(os.environ['SQLITE_CONNECTION_STRING'])
    except KeyError:
        # db = MySQLDatabase(
        #     database=os.environ['MYSQL_DATABASE'],
        #     user=os.environ['MYSQL_USER'],
        #     password=os.environ['MYSQL_PASSWORD'],
        #     host=os.environ['MYSQL_HOST'],
        #     port=3306
        # )
        db = PooledPostgresqlExtDatabase(
            database=os.environ['POSTGRES_DB'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            host=os.environ['POSTGRES_HOST'],
            port=5432
        )

    return db


class BaseModel(Model):
    class Meta:
        database = get_db()
        model_metadata_class = ThreadSafeDatabaseMetadata


class Submissions(BaseModel):
    id = CharField(unique=True)
    author = CharField()
    created_utc = IntegerField()
    num_comments = IntegerField()
    over_18 = BooleanField()
    permalink = CharField()
    score = IntegerField()
    subreddit = CharField()
    title = TextField()
    selftext = TextField(null=False)
    modification_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        primary_key = CompositeKey('subreddit', 'id')


class SubmissionsPushshift(BaseModel):
    id = CharField(unique=True)
    author = CharField()
    created_utc = IntegerField()
    num_comments = IntegerField()
    over_18 = BooleanField()
    permalink = CharField()
    score = IntegerField()
    subreddit = CharField()
    title = TextField()
    selftext = TextField(null=False)
    modification_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        primary_key = CompositeKey('subreddit', 'id')


class Comments(BaseModel):
    submission_id = CharField()
    author = CharField(null=True)
    id = CharField()
    score = IntegerField()
    parent_id = CharField()
    body = TextField()
    modification_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        primary_key = CompositeKey('submission_id', 'id')


class Errors(BaseModel):
    typ = CharField()
    params = TextField()
    info = TextField()
    modification_time = DateTimeField(default=datetime.datetime.now)



db = get_db()
db.connect()
db.bind([Submissions, Comments, Errors, SubmissionsPushshift])
db.create_tables([Submissions, Comments, Errors, SubmissionsPushshift])
db.close()


@db.atomic()
def insert_submissions(data_dict):
    return Submissions.insert_many(data_dict).on_conflict(action='IGNORE').execute()


@db.atomic()
def insert_submissions_pushshift(data_dict):
    return SubmissionsPushshift.insert_many(data_dict).on_conflict(action='IGNORE').execute()


@db.atomic()
def insert_comments(data_dict):
    return Comments.insert_many(data_dict).on_conflict(action='IGNORE').execute()


@db.atomic()
def insert_error(**kwargs):
    return Errors.insert(
        typ=kwargs.pop('typ'),
        params=kwargs.pop('params'),
        info=kwargs.pop('info')
    ).execute()
