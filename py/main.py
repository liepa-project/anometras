# src/main.py

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.commons.postgres import database
from src.elan_file.elan_file_route import elan_file_router
from fastapi.responses import HTMLResponse






@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

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