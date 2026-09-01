# ❤❤ Zhao's Homepage & Local AI Hub!❤❤
# 🚀 My First Release v1.0.0


개인 웹 허브와 로컬 AI 인터페이스를 하나의 FastAPI 애플리케이션으로 엮은 실험적 멀티미디어 프로젝트입니다. 사진 공유, 영상 자막 생성, 음악이 결합된 시계 페이지, 그리고 Live2D 기반 대화형 AI 캐릭터 **Mio**를 단일 진입점에서 제공합니다.

## Highlights

- **Mio AI VTuber** — Live2D `mao_pro` 모델과 음성·텍스트 대화를 결합한 로컬 캐릭터 인터페이스
- **On-demand backend** — `/mioai/` 첫 접속 시 MioAI WebSocket 서버를 자동으로 시작해, 별도 실행 단계를 줄였습니다.
- **Subtitle workspace** — Whisper 기반 음성 인식으로 미디어 자막 생성을 지원하는 Flask 보조 서비스
- **Personal media hub** — 사진 업로드 갤러리, 배경음악과 인터랙티브 시계 등 가벼운 개인 웹 기능
- **Self-hosted by design** — 로컬 네트워크에서 실행할 수 있도록 FastAPI 정적 파일 서빙과 경로 구성을 단순화했습니다.

## Architecture

```text
Browser
  └─ FastAPI (pictures.py, :8000)
       ├─ /            Personal homepage
       ├─ /send        Photo gallery
       ├─ /subtitle    Subtitle tool launcher
       ├─ /cm          Clock and music page
       └─ /mioai/      Mio frontend → auto-starts MioAI (:12393)
```

## Quick start

### 1. Configure MioAI

The real configuration file is intentionally excluded from Git because it can contain API keys.

```powershell
cd templates\mioai
Copy-Item conf.example.yaml conf.yaml
```

Open `conf.yaml`, select a supported LLM provider, and enter only your own API key. Do not commit this file.

### 2. Install MioAI dependencies

```powershell
cd templates\mioai
uv sync
```

### 3. Start the web hub

```powershell
cd ..\..
uvicorn pictures:app --host 0.0.0.0 --port 8000 --reload
```

Open [http://localhost:8000](http://localhost:8000). Visiting `/mioai/` starts the MioAI server automatically; its first startup may take a moment while local resources initialize.

## Privacy and repository policy

- API credentials remain only in local `templates/mioai/conf.yaml`.
- Chat histories, runtime logs, generated subtitle audio, photo uploads, downloaded models, and virtual environments are excluded from Git.
- This repository ships only the `mao_pro` Live2D character asset. Do not add proprietary models unless their redistribution license permits it.

## Tech stack

Python · FastAPI · Flask · Uvicorn · Jinja2 · Open-LLM-VTuber · Live2D Cubism · Whisper / faster-whisper · JavaScript · HTML/CSS

## License notes

The MioAI portion includes third-party components and Live2D assets. Review the included license files—especially `templates/mioai/LICENSE-Live2D.md`—before redistribution or commercial use.

### 저작권
MIO.ai : openllmvtuber / https://github.com/Open-LLM-VTuber/Open-LLM-VTuber\

character zzz zhao : https://zenless.hoyoverse.com/

zhao emoji : dcincide, arcarlve   / https://gall.dcinside.com/mgallery/board/lists/?id=zenless_zone_zero / https://arca.live/b/zenlesszonezero
