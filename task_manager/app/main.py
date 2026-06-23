from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import logging
from .database import engine, Base
from .routers import auth, tasks

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskManager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 500:
        error_id = str(uuid.uuid4())
        logging.exception(f"HTTP 500 Exception (Error ID: {error_id}): {exc.detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error. Traceback ID: {error_id}"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logging.exception(f"Unhandled Exception (Error ID: {error_id})")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error. Traceback ID: {error_id}"}
    )

app.include_router(auth.router)
app.include_router(tasks.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the TaskManager API"}
