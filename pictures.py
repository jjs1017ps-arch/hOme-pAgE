import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
MIOAI_DIR = BASE_DIR / "templates" / "mioai"
MIOAI_FRONTEND_DIR = MIOAI_DIR / "frontend"
MIOAI_PORT = 12393
_mioai_process: subprocess.Popen | None = None
_mioai_process_lock = threading.Lock()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _mioai_server_is_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", MIOAI_PORT), timeout=0.2):
            return True
    except OSError:
        return False


def ensure_mioai_server_started() -> None:
    """Start MioAI on the first /mioai visit unless it is already running."""
    global _mioai_process

    with _mioai_process_lock:
        if _mioai_server_is_running():
            return

        if _mioai_process is None or _mioai_process.poll() is not None:
            _mioai_process = subprocess.Popen(
                ["uv", "run", "run_server.py"],
                cwd=MIOAI_DIR,
            )
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")
from fastapi.responses import FileResponse

@app.get("/mioai/undefined/undefined.model3.json")
def load_mao_model():
    return FileResponse(
        BASE_DIR / "templates" / "mioai" / "live2d-models" / "mao_pro" / "runtime" / "mao_pro.model3.json"
    )

# photos 폴더가 없으면 생성1
if not os.path.exists("photos"):
    os.makedirs("photos")

# photos 폴더를 /images 주소로 공개
app.mount("/images", StaticFiles(directory="photos"), name="images")
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


app.mount(
    "/song",
    StaticFiles(directory=BASE_DIR / "song"),
    name="song"
)

# 메인
@app.get("/")
def home(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="homepage/index.html",
            context={}
        )

@app.get("/cm")
def cm(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="cm/index.html",
        context={}
    )

import subprocess
import sys
import os


@app.get("/subtitle")
def subtitle(request: Request):
    subprocess.Popen([
        sys.executable,
        str(BASE_DIR / "templates" / "subtitle" / "app.py")
    ])

    return templates.TemplateResponse(
        request=request,
        name="subtitle/index.html",
        context={}
    )


@app.get("/mioai/")
def mioai():
    ensure_mioai_server_started()
    return FileResponse(MIOAI_FRONTEND_DIR / "index.html")


from fastapi.staticfiles import StaticFiles
app.mount(
    "/mioai",
    StaticFiles(
        directory=MIOAI_FRONTEND_DIR,
        html=True
    ),
    name="mioai",
)

app.mount(
    "/live2d-models",
    StaticFiles(
        directory=MIOAI_DIR / "live2d-models"
    ),
    name="live2d-models",
)
app.mount(
    "/mioai/live2d-models",
    StaticFiles(
        directory=MIOAI_DIR / "live2d-models"
    ),
    name="live2d-models",
)
# 사진 목록 + 업로드 화면
@app.get("/send")
def send():

    files = os.listdir("photos")

    html_content = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>컴퓨터 사진 갤러리</title>   

        <style>
            body {
                font-family: sans-serif;
                text-align: center;
                background-color: #f0f2f5;
                padding: 20px;
                margin: 0;
            }

            .upload-box {
                background: white;
                padding: 20px;
                border-radius: 12px;
                max-width: 400px;
                margin: 0 auto 20px auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }

            .upload-box h2 {
                margin-top: 0;
                color: #333;
            }

            .file-btn {
                margin-bottom: 10px;
            }

            .submit-btn {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                width: 100%;
            }

            .submit-btn:hover {
                background-color: #0056b3;
            }

            .gallery-item {
                background: white;
                padding: 15px;
                margin: 15px auto;
                border-radius: 10px;
                max-width: 400px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .gallery-item p {
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
                word-break: break-all;
            }

            .gallery-item img {
                width: 100%;
                height: auto;
                border-radius: 5px;
            }

            .delete-btn {
                margin-top: 10px;
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
            }

            .delete-btn:hover {
                background-color: #b02a37;
            }

            hr {
                max-width: 440px;
                margin: 30px auto;
                border: 0;
                height: 1px;
                background: #ccc;
            }
        </style>
    </head>

    <body>

        <div class="upload-box">

            <h2>📤 사진 컴퓨터로 보내기</h2>

            <form action="/upload" method="post" enctype="multipart/form-data">

                <input
                    type="file"
                    name="file"
                    accept="image/*"
                    class="file-btn"
                    required
                >

                <br>

                <button type="submit" class="submit-btn">
                    업로드 하기
                </button>

            </form>

        </div>

        <hr>

        <h1>📸 컴퓨터 사진 목록</h1>
    """

    image_count = 0

    for file in files:

        if file.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".webp")
        ):

            html_content += f"""
            <div class="gallery-item">

                <p>{file}</p>

                <img
                    src="/images/{file}"
                    alt="{file}"
                >

                <form
                    action="/delete/{file}"
                    method="post"
                    onsubmit="return confirm('정말 삭제할까요?');"
                >

                    <button type="submit" class="delete-btn">
                        🗑️ 삭제
                    </button>

                </form>

            </div>
            """

            image_count += 1

    if image_count == 0:
        html_content += """
        <p style="color:gray;">
            photos 폴더 안에 사진 파일이 없습니다!
        </p>
        """

    html_content += """
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


# 사진 업로드
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):

    # 1. photos 폴더에 있는 파일 확인
    files = os.listdir("photos")

    original_name = file.filename

    # 2. 다음 사진 번호 정하기
    filename = f"{len(files)+1}.{original_name}"

    # 3. 저장할 위치 정하기
    destination_path = os.path.join(
        "photos",
        filename
    )

    # 4. 실제로 사진 저장
    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 5. 업로드가 끝났다고 응답
    return HTMLResponse("""
        <script>
            console.log("사진 업로드 완료!");
            location.href = "/send";
        </script>
    """)


# 사진 삭제
@app.post("/delete/{filename}")
def delete_file(filename: str):
    file_path = os.path.join("photos", filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    return HTMLResponse("""
        <script>
            console.log("사진이 삭제되었습니다!");
            location.href = "/send";
        </script>
    """)

# 서버 실행
if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
