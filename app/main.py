"""
Главный файл FastAPI приложения Мир Самозанятых v8.1
АНО ЦПС ИНН 9724016805
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import logger
from app.core.security import generate_csp_nonce

from app.api import auth, users, sales, contracts, crm, svetlana, websocket, subscriptions, flutter, email_campaigns, analytics, import_export, search, calendar, notifications, webrtc, ai_analytics, white_label, mfa, telegram_bot, api_keys, webhooks, whatsapp, reports, backups, health, admin, referrals, tasks, export, import_data, accounting, fns, bank

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    yield
    await close_db()
    logger.info("👋 Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Платформа для самозанятых. АНО ЦПС ИНН 9724016805",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, f"https://{settings.DOMAIN}"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[settings.DOMAIN, f"*.{settings.DOMAIN}", "localhost", "127.0.0.1"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    nonce = generate_csp_nonce()
    request.state.csp_nonce = nonce
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'; "
        f"font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; "
        f"connect-src 'self' https://api.openrouter.ai https://api.yookassa.ru; frame-ancestors 'none'; "
        f"base-uri 'self'; form-action 'self';"
    )
    response.headers["X-Response-Time"] = f"{duration:.2f}ms"
    return response


@app.middleware("http")
async def request_logging(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} {duration:.2f}ms {request.client.host}",
            extra={"method": request.method, "path": request.url.path, "status": response.status_code, "duration_ms": round(duration, 2), "ip_address": request.client.host, "user_agent": request.headers.get("user-agent", "")[:100]},
        )
        return response
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"{request.method} {request.url.path} ERROR {duration:.2f}ms: {e}",
            extra={"method": request.method, "path": request.url.path, "duration_ms": round(duration, 2), "ip_address": request.client.host},
        )
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": True, "status": exc.status_code, "message": exc.detail, "path": request.url.path, "timestamp": datetime.now(timezone.utc).isoformat()})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": True, "status": 500, "message": "Внутренняя ошибка сервера" if not settings.DEBUG else str(exc), "path": request.url.path, "timestamp": datetime.now(timezone.utc).isoformat()})


for router in [auth, users, sales, contracts, crm, svetlana, websocket, subscriptions, flutter, email_campaigns, analytics, import_export, search, calendar, notifications, webrtc, ai_analytics, white_label, mfa, telegram_bot, api_keys, webhooks, whatsapp, reports, backups, health, referrals, tasks, export, import_data, accounting, fns, bank]:
    app.include_router(router.router)


@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "healthy", "version": settings.APP_VERSION, "timestamp": datetime.now(timezone.utc).isoformat(), "environment": settings.ENVIRONMENT}


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    nonce = request.state.csp_nonce
    return HTMLResponse(f'''<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{settings.APP_NAME}</title><style nonce="{nonce}">*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:linear-gradient(135deg,#0D47A1 0%,#1976D2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;color:white}}.container{{text-align:center;padding:40px;max-width:600px}}h1{{font-size:3rem;margin-bottom:16px;font-weight:700}}p{{font-size:1.2rem;opacity:.9;margin-bottom:32px}}.version{{display:inline-block;background:rgba(255,255,255,.15);padding:8px 20px;border-radius:20px;font-size:.9rem;backdrop-filter:blur(10px)}}.links{{margin-top:32px;display:flex;gap:16px;justify-content:center;flex-wrap:wrap}}.links a{{color:white;text-decoration:none;padding:12px 24px;border:1px solid rgba(255,255,255,.3);border-radius:8px}}</style></head><body><div class="container"><h1>Мир Самозанятых</h1><p>Платформа для самозанятых и фрилансеров</p><span class="version">v{settings.APP_VERSION}</span><div class="links"><a href="/docs">API Docs</a><a href="/health">Health</a></div></div></body></html>''')
