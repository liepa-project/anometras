# src/main.py

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from common.postgres import database
from common import message_broker as mb
from .elan_file.elan_file_route import elan_file_router
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger('uvicorn.error')






@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await mb.broker.connect()
    logger.debug('[lifespan] connected')
    yield
    await database.disconnect()
    await mb.broker.disconnect()

app = FastAPI(lifespan=lifespan)

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