import pathlib
import io
import uuid
import pytesseract

from functools import lru_cache
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings
from PIL import Image

BASE_DIR = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"


class Settings(BaseSettings):
    debug: bool = False
    echo_active: bool = False
    app_auth_token: str
    app_auth_token_prod: str = None
    skip_auth: bool = False

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def verify_auth(
    authorization=Header(None),
    settings: Settings = Depends(get_settings),
):
    if settings.debug and settings.skip_auth:
        return
    if authorization is None:
        raise HTTPException(detail="Invalid authorization", status_code=401)
    label, token = authorization.split()
    if token != settings.app_auth_token:
        raise HTTPException(detail="Invalid authorization", status_code=401)


@app.post("/")
async def prediction_view(
    file: UploadFile = File(...),
    authorization=Header(None),
    settings: Settings = Depends(get_settings),
):
    verify_auth(authorization, settings)
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str)
    except:
        raise HTTPException(detail="Invalid file format", status_code=400)

    preds = pytesseract.image_to_string(img)
    predictions = [x for x in preds.split("\n")]
    return {"results": predictions, "original": preds}


@app.post("/img-echo/", response_class=FileResponse)
async def img_echo_view(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings)
):
    if settings.echo_active:
        UPLOAD_DIR.mkdir(exist_ok=True)
        bytes_str = io.BytesIO(await file.read())
        try:
            image = Image.open(bytes_str)
        except:
            raise HTTPException(detail="Invalid file format", status_code=400)
        fname = pathlib.Path(file.filename)
        dest = UPLOAD_DIR / f"{uuid.uuid1()}{fname.suffix}"
        image.save(dest)
        return dest
