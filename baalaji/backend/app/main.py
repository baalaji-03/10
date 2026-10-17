import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.seed import seed_database_defaults

# Import all routers
from backend.app.routers import (
    auth, dashboard, medicines, purchases, pos,
    customers, suppliers, alerts, returns,
    reports, expenses, excel, invoices, settings as app_settings
)

logger = logging.getLogger("pharmacy_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.database_status = "connecting"
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database_defaults(db)
        finally:
            db.close()
        app.state.database_status = "ready"
        logger.info("Database initialized and ready.")
    except Exception as e:
        app.state.database_status = "unavailable"
        logger.warning(f"Database initialization warning during startup: {e}")
    yield
    # Shutdown logic if needed

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error(
        "Database request failed for %s",
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__)
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is unavailable. Check the backend runtime logs and DATABASE_URL."}
    )

# Include API Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(medicines.router)
app.include_router(purchases.router)
app.include_router(pos.router)
app.include_router(customers.router)
app.include_router(suppliers.router)
app.include_router(alerts.router)
app.include_router(returns.router)
app.include_router(reports.router)
app.include_router(expenses.router)
app.include_router(excel.router)
app.include_router(invoices.router)
app.include_router(app_settings.router)

# Mount frontend directory for Web & Electron app
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/health")
@app.get("/api/health")
def health_check():
    database_status = getattr(app.state, "database_status", "not_initialized")
    status_code = 200 if database_status == "ready" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if database_status == "ready" else "degraded",
            "database": database_status,
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    )

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")
