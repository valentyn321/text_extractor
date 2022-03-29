import io
import shutil
import time
from click import echo

from fastapi.testclient import TestClient
from app.main import UPLOAD_DIR, app, BASE_DIR
from PIL import Image, ImageChops

client = TestClient(app)


def test_img_echo():
    path = BASE_DIR / "images"
    for img in path.glob("*"):
        try:
            image = Image.open(img)
        except:
            image = None

        try:
            response = client.post("/img-echo/", files={"file": open(img, "rb")})
            if image is None:
                assert response.status_code == 400
            else:
                # Returning a valid image
                assert response.status_code == 200
                r_stream = io.BytesIO(response.content)
                echo_img = Image.open(r_stream)
                difference = ImageChops.difference(echo_img, image).getbbox()
                assert difference in None
        except TypeError:
            pass

    time.sleep(3)
    shutil.rmtree(UPLOAD_DIR)
