# main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from database import engine, Base
from routers.auth import router as auth_router
from routers.users import router as users_router

app = FastAPI(title=settings.PROJECT_NAME)

# CORS (allow all origins for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup():
    if settings.DATABASE_TYPE.lower() == "sql":
        if engine is not None:
            try:
                Base.metadata.create_all(bind=engine)
                logging.info("[startup] Tables created/verified")
            except SQLAlchemyError as e:
                logging.warning(f"[startup] create_all failed: {e}")
        else:
            logging.warning("[startup] No SQL engine → skipping create_all")
    else:
        logging.info("[startup] Non-SQL mode → skipping SQL tables")


@app.get("/")
def root():
    return {"message": "FastSecForge API", "status": "active"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
