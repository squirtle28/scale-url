"""
ScaleURL FastAPI application entrypoint.

This module only wires things together: create the app, register
routers. Three separate processes run this same module (backend1,
backend2, backend3 in docker-compose) behind NGINX; none of them share
in-memory state, so any of them can handle any request.
"""

from fastapi import FastAPI

from app.routers import health, urls

app = FastAPI(
    title="ScaleURL",
    description="A production-inspired URL shortening service.",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(urls.router)
app.include_router(urls.redirect_router)
