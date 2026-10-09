import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from threading import Thread
from typing import List  # noqa: UP035

from app.api.v2_0.request import SearchRequest
from app.core.search import search

logger = logging.getLogger(__name__)

SEARCH_CACHE_TTL = 3600


@dataclass
class SearchJob:
    id: str
    status: str = "running"
    providers_total: int = 0
    providers_completed: List[str] = field(default_factory=list)
    # hits: List[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_redis(job_id: str, data: dict):
        # logger.debug(data)
        return SearchJob(
            id=job_id,
            status=data.get("status", "running"),
            providers_total=int(data.get("providers_total", 0)),
            providers_completed=json.loads(data.get("providers_completed", "[]")),
            results=json.loads(data.get("results", "[]")),
        )


def get_search_job(redis, job_id: str) -> SearchJob | None:
    key = f"search:{job_id}"
    data = redis.hgetall(key)

    if not data:
        return None
    
    return SearchJob.from_redis(job_id, data)


def run_search_job(redis, providers, job_id: str, request: SearchRequest):

    key = f"search:{job_id}"
    providers_completed = []
    results = {}

    try:
        for event in search(providers, request):
            provider_name = event["provider"]
            if provider_name not in providers_completed:
                providers_completed.append(provider_name)

            logger.debug(event)
            results[provider_name] = event["results"]
            logger.debug(results)
            redis.hset(key, mapping={
                "providers_completed": json.dumps(providers_completed),
                "status": "running",
            })
        redis.hset(key, mapping={
            "status": "done",
            "providers_completed": json.dumps(providers_completed),
            "results": json.dumps(results),
        })
    except Exception as e:
        logger.debug(str(e))
        redis.hset(key, mapping={
            "status": "error",
            "error": str(e),
        })


def start_search_job(redis, providers, request: SearchRequest) -> str:

    query_data = request.model_dump(mode="json")
    query_data["providers"] = sorted(provider.code_name for provider in providers)
    # caching query key
    query_key = "search:query:" + hashlib.sha256(
        json.dumps(
            query_data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    # check if job exists
    existing_job_id = redis.get(query_key)
    if existing_job_id:
        existing_job = get_search_job(redis, existing_job_id)
        if existing_job and existing_job.status in {"running", "done"}:
            return existing_job_id

    job_id = str(uuid.uuid4())
    key = f"search:{job_id}"

    redis.hset(key, mapping={
        "status": "running",
        "providers_total": len(providers),
        "providers_completed": json.dumps([]),
    })
    redis.set(query_key, job_id, ex=SEARCH_CACHE_TTL)

    Thread(
        target=run_search_job,
        args=(redis, providers, job_id, request),
        daemon=True
    ).start()

    return job_id
