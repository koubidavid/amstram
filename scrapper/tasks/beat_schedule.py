import json
import os

import redis as redis_lib

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CRON_REGISTRY_KEY = "amstram:cron_registry"

beat_schedule = {}
beat_schedule_filename = "celerybeat-schedule"
timezone = "Europe/Paris"


def _get_redis():
    return redis_lib.from_url(REDIS_URL)


def register_cron(job_id: str, cron_expression: str):
    r = _get_redis()
    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression, expected 5 parts: min hour day month dow")
    r.hset(CRON_REGISTRY_KEY, job_id, json.dumps({
        "minute": parts[0], "hour": parts[1],
        "day_of_month": parts[2], "month_of_year": parts[3],
        "day_of_week": parts[4],
    }))


def unregister_cron(job_id: str):
    r = _get_redis()
    r.hdel(CRON_REGISTRY_KEY, job_id)


def load_dynamic_schedules():
    from celery.schedules import crontab
    r = _get_redis()
    crons = r.hgetall(CRON_REGISTRY_KEY)
    for job_id, schedule_json in crons.items():
        schedule = json.loads(schedule_json)
        beat_schedule[f"cron-{job_id.decode()}"] = {
            "task": "tasks.run_full_scraping",
            "schedule": crontab(**schedule),
            "args": [job_id.decode()],
        }


try:
    load_dynamic_schedules()
except Exception:
    pass
