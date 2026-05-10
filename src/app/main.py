from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, courses, enrollments, lessons, quizzes, certificates, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Online Learning Platform",
    description="Платформа онлайн-обучения — API для управления курсами, уроками, тестами и сертификатами",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(enrollments.router, prefix="/api/v1")
app.include_router(quizzes.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {
        "message": "Online Learning Platform API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
