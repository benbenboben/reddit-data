
from peewee import *
import datetime
import os


db = SqliteDatabase(os.environ.get('DB_CONNECTION_STRING'))


class BaseModel(Model):
    class Meta:
        database = db


class Submissions(BaseModel):
    id = CharField(unique=True)
    author = CharField()
    created_utc = DateTimeField()
    num_comments = IntegerField()
    over_18 = BooleanField()
    permalink = CharField()
    score = IntegerField()
    subreddit = CharField()
    title = TextField()
    selftext = TextField(null=True)
    modification_time = DateTimeField(default=datetime.datetime.now)

    class Meta:
        primary_key = CompositeKey('subreddit', 'id')


class Comments(BaseModel):
    submission_id = CharField()
    author = CharField()
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


db.connect()
db.create_tables([Submissions, Comments, Errors])