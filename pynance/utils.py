import requests
from datetime import datetime


def to_milliseconds(seconds):
    return 1e+3 * seconds


def to_seconds(milliseconds):
    return 1e-3 * milliseconds


def create_datetime(timestamp_ms):
    return datetime.fromtimestamp(to_seconds(timestamp_ms))


def create_session(api_key):

    headers = {"X-MBX-APIKEY": api_key}

    session = requests.Session()
    session.headers.update(headers)

    return session


def create_timestamp(dt=datetime.now()):
    return int(to_milliseconds(dt.timestamp()))
