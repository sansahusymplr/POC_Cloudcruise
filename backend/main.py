from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import autofill, mappings, practitioners, sessions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="POC CloudCruise Autofill", version="0.1.0")

app.include_router(mappings.router)
app.include_router(practitioners.router)
app.include_router(autofill.router)
app.include_router(sessions.router)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
