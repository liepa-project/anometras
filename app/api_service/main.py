# src/main.py

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from common.postgres import database
from common import message_broker as mb
from .elan_file.elan_file_route import elan_file_router
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



import logging

logger = logging.getLogger('uvicorn.error')






@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    mb.broker.connect()
    logger.debug('[lifespan] connected')
    yield
    await database.disconnect()
    await mb.broker.disconnect()

app = FastAPI(lifespan=lifespan)

origins = [
    "*"
    # "http://localhost",
    # "http://localhost:8080",
    # "http://localhost:8002",
    # "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="/app/api_service/static", html=True), name="static")

favicon_path = 'static/favicons/favicon.ico'

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

app.include_router(elan_file_router)

@app.get("/rapidoc", response_class=HTMLResponse, include_in_schema=False)
async def rapidoc():
    return f"""
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <script 
                    type="module" 
                    src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"
                ></script>
            </head>
            <body>
                <rapi-doc spec-url="{app.openapi_url}"></rapi-doc>
            </body> 
        </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")