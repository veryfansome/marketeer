from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import os

from marketeer.data.ebay.ebay_fetcher import fetch as ebay_fetch
from observability.logging import logging, setup_logging
from settings import app_settings

scheduler = AsyncIOScheduler()

##
# Logging

setup_logging()
logger = logging.getLogger(__name__)


##
# App


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Service startup/shutdown behavior.

    :param app:
    :return:
    """

    await ebay_fetch()
    scheduler.add_job(ebay_fetch, 'interval', seconds=app_settings.EBAY_FETCH_INTERVAL_SECONDS, name='fetch:eBay')
    scheduler.start()
    # Started
    yield
    # Stopping
    pass


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
if os.path.exists("app/static/tests"):
    app.mount("/tests", StaticFiles(directory="app/static/tests"), name="tests")
    app.mount("/tests/cov", StaticFiles(directory="app/static/tests/cov"), name="tests_cov")


##
# Endpoints

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    file_path = os.path.join(os.path.dirname(__file__), 'static', 'favicon.ico')
    return FileResponse(file_path)


@app.get("/", include_in_schema=False)
async def get_landing():
    file_path = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
    return FileResponse(file_path)


@app.get("/healthz")
async def get_healthz():
    return {"status": "OK"}


@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
