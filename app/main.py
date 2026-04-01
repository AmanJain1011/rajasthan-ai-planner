from fastapi import FastAPI
from app.db import Base, engine
from app.routes.places import router as places_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rajasthan AI Planner", version="0.1.0")
app.include_router(places_router, prefix="/api")
