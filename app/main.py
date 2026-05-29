from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.categories import router as categories_router
from backend.app.api.properties import router as properties_router
from backend.app.api.products import router as products_router
from backend.app.api.uploads import router as uploads_router
from backend.app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)
app.include_router(properties_router)
app.include_router(products_router)
app.include_router(uploads_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
