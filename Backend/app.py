from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from auth import auth_bp
from extensions import db
from runtime import set_runtime_config
from tax_api import tax_bp


load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

from config import Config


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    set_runtime_config(Config)
    Path(Config.PDF_EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    db.init_app(Config)
    db.create_all()
    yield
    db.session.remove()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def db_session_middleware(request, call_next):
        try:
            response = await call_next(request)
        finally:
            db.session.remove()
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        del request
        return JSONResponse({"message": str(exc.detail)}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        del request
        detail = exc.errors()[0].get("msg", "Invalid request.") if exc.errors() else "Invalid request."
        return JSONResponse({"message": detail}, status_code=422)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(auth_bp)
    app.include_router(tax_bp)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
