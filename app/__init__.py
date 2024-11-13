from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .google import google_routes


app = FastAPI(root_path='/api/v1')

app.include_router(google_routes)

@app.get('/')
async def read_root(request: Request):
    protocol = request.url.scheme
    host = request.url.hostname
    port = request.url.port
    return JSONResponse(content=f"Server is running at {protocol}://{host}:{port}", status_code=200)