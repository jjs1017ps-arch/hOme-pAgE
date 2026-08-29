    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    from faster_whisper import WhisperModel
    import yt_dlp
    import os
    import uuid
    import json
    import re
    import html
    import urllib.request
    
    # ==================================================
    # Flask 기본 설정
    # ==================================================
    
    app = Flask(__name__)
    CORS(app)
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    
    # ==================================================
    # Whisper
    # ==================================================
    
    print()
    print("==============================")
    print("       Subtitle AI")
    print("==============================")
    print()
    
    print("[로그] Whisper 모델 불러오는 중...")
    
    try:
        model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
            cpu_threads=3
        )
    
        print("[로그] Whisper 모델 준비 완료")
    
    except Exception as e:
        print("[오류] Whisper 모델을 불러오지 못했습니다.")
        print(e)
        input("엔터를 누르면 종료됩니다...")
        raise
    
    
    # ==================================================
    # 메인 페이지
    # ==================================================
    
    @app.route("/")
    def index():
        return send_from_directory(
            BASE_DIR,
            "index.html"
        )
    
    
    # ==================================================
    # 배경 이미지
    # ==================================================
    
    @app.route("/space<int:number>.jpg")
    def background(number):
    
        if number < 1 or number > 4:
            return "Not Found", 404
    
        filename = f"space{number}.jpg"
    
        filepath = os.path.join(
            BASE_DIR,
            filename
        )
    
        if not os.path.isfile(filepath):
            return "Not Found", 404
    
        return send_from_directory(
            BASE_DIR,
            filename
        )
    
    
    # ==================================================
    # 직접 작성된 유튜브 자막 파싱
    # ==================================================
    
    def parse_youtube_subtitle(url):
    
        try:
    
            print("[로그] 직접 작성된 자막 다운로드 중...")
    
            with urllib.request.urlopen(
                    url,
                    timeout=30
            ) as response:
    
                data = response.read().decode("utf-8")
    
            subtitles = []
    
            # ==================================================
            # TTML 형식
            # ==================================================
    
            text_matches = re.findall(
                r'<text start="([^"]+)" dur="([^"]+)"[^>]*>(.*?)</text>',
                data,
                re.DOTALL
            )
    
            for start_text, duration_text, text in text_matches:
    
                try:
    
                    start = float(start_text)
                    duration = float(duration_text)
    
                except ValueError:
    
                    continue
    
                # HTML 태그 제거
                text = re.sub(
                    r"<[^>]+>",
                    "",
                    text
                )
    
                # HTML 엔티티 복원
                text = html.unescape(text)
    
                # 줄바꿈 처리
                text = text.replace(
                    "\n",
                    " "
                )
    
                text = text.strip()
    
                if not text:
                    continue
    
                subtitles.append({
                    "start": start,
                    "end": start + duration,
                    "text": text
                })
    
            if subtitles:
                return subtitles
    
    
            # ==================================================
            # JSON3 형식
            # ==================================================
    
            try:
    
                json_data = json.loads(data)
    
                events = json_data.get(
                    "events",
                    []
                )
    
                for event in events:
    
                    if "segs" not in event:
                        continue
    
                    text_parts = []
    
                    for seg in event["segs"]:
    
                        text_parts.append(
                            seg.get(
                                "utf8",
                                ""
                            )
                        )
    
                    text = "".join(
                        text_parts
                    ).strip()
    
                    if not text:
                        continue
    
                    start = (
                            event.get(
                                "tStartMs",
                                0
                            ) / 1000
                    )
    
                    duration = (
                            event.get(
                                "dDurationMs",
                                0
                            ) / 1000
                    )
    
                    subtitles.append({
                        "start": float(start),
                        "end": float(
                            start + duration
                        ),
                        "text": text
                    })
    
            except Exception:
                pass
    
            return subtitles
    
        except Exception as e:
    
            print(
                f"[로그] 자막 다운로드 실패: {e}"
            )
    
            return []
    
    
    # ==================================================
    # YouTube 직접 작성 자막 찾기
    # ==================================================
    
    def find_manual_subtitles(info):
    
        subtitles_info = info.get(
            "subtitles",
            {}
        )
    
        if not subtitles_info:
            return []
    
        # 원하는 언어 우선순위
        language_order = [
            "ko",
            "ko-KR",
            "ja",
            "ja-JP",
            "en",
            "en-US",
            "zh-Hans",
            "zh-CN",
            "zh"
        ]
    
        selected_language = None
    
        # ==================================================
        # 우선 원하는 언어 찾기
        # ==================================================
    
        for language in language_order:
    
            if language in subtitles_info:
    
                selected_language = language
                break
    
    
        # ==================================================
        # 원하는 언어가 없으면 아무 자막 사용
        # ==================================================
    
        if selected_language is None:
    
            for language in subtitles_info:
    
                if language:
    
                    selected_language = language
                    break
    
    
        if selected_language is None:
            return []
    
    
        print(
            f"[로그] 직접 작성된 자막 발견: "
            f"{selected_language}"
        )
    
    
        formats = subtitles_info.get(
            selected_language,
            []
        )
    
        if not formats:
            return []
    
    
        # ==================================================
        # JSON3 우선
        # ==================================================
    
        selected_format = None
    
        for subtitle_format in formats:
    
            if subtitle_format.get(
                    "ext"
            ) == "json3":
    
                selected_format = subtitle_format
                break
    
    
        # ==================================================
        # JSON3가 없으면 첫 번째 형식
        # ==================================================
    
        if selected_format is None:
    
            selected_format = formats[0]
    
    
        subtitle_url = selected_format.get(
            "url"
        )
    
        if not subtitle_url:
            return []
    
    
        return parse_youtube_subtitle(
            subtitle_url
        )
    
    
    # ==================================================
    # YouTube 분석
    # ==================================================
    
    @app.route(
        "/youtube",
        methods=["POST"]
    )
    def youtube():
    
        try:
    
            data = request.get_json()
    
            if not data:
    
                return jsonify({
                    "error": "요청 데이터가 없습니다."
                }), 400
    
    
            url = data.get(
                "url"
            )
    
            if not url:
    
                return jsonify({
                    "error": "YouTube URL이 없습니다."
                }), 400
    
    
            job_id = str(
                uuid.uuid4()
            )
    
    
            output_template = os.path.join(
                DOWNLOAD_DIR,
                f"{job_id}.%(ext)s"
            )
    
    
            # ==================================================
            # YouTube 정보 확인
            # ==================================================
    
            print()
            print(
                "[로그] 유튜브 정보 확인 중..."
            )
    
    
            info_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
    
                # 자동 생성 자막 제외
                "writesubtitles": False,
                "writeautomaticsub": False
            }
    
    
            with yt_dlp.YoutubeDL(
                    info_opts
            ) as ydl:
    
                info = ydl.extract_info(
                    url,
                    download=False
                )
    
    
            title = info.get(
                "title",
                "제목 없음"
            )
    
    
            print(
                f"[로그] 제목: {title}"
            )
    
    
            # ==================================================
            # 직접 작성 자막 확인
            # ==================================================
    
            print(
                "[로그] 직접 작성된 자막 확인 중..."
            )
    
    
            subtitles = find_manual_subtitles(
                info
            )
    
    
            # ==================================================
            # 음원 다운로드
            # ==================================================
    
            print(
                "[로그] 음원 다운로드 시작"
            )
    
    
            audio_opts = {
    
                "format": "bestaudio/best",
    
                "outtmpl": output_template,
    
                "noplaylist": True,
    
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192"
                    }
                ]
            }
    
    
            with yt_dlp.YoutubeDL(
                    audio_opts
            ) as ydl:
    
                ydl.extract_info(
                    url,
                    download=True
                )
    
    
            # ==================================================
            # MP3 확인
            # ==================================================
    
            audio_path = os.path.join(
                DOWNLOAD_DIR,
                f"{job_id}.mp3"
            )
    
    
            if not os.path.exists(
                    audio_path
            ):
    
                print(
                    "[오류] MP3 파일을 찾을 수 없습니다."
                )
    
                return jsonify({
                    "error": "MP3 파일을 찾을 수 없습니다."
                }), 500
    
    
            # ==================================================
            # 직접 작성 자막이 없으면 Whisper
            # ==================================================
    
            if not subtitles:
    
                print(
                    "[로그] 직접 작성된 자막이 없습니다."
                )
    
                print(
                    "[로그] Whisper를 사용합니다."
                )
    
                print(
                    "[로그] Whisper 분석 시작"
                )
    
    
                segments, whisper_info = model.transcribe(
    
                    audio_path,
    
                    beam_size=5,
    
                    vad_filter=True
                )
    
    
                subtitles = []
    
    
                for segment in segments:
    
                    text = segment.text.strip()
    
                    if not text:
                        continue
    
    
                    subtitles.append({
    
                        "start":
                            float(
                                segment.start
                            ),
    
                        "end":
                            float(
                                segment.end
                            ),
    
                        "text":
                            text
                    })
    
    
                print(
                    f"[로그] Whisper 자막 "
                    f"{len(subtitles)}개 생성 완료"
                )
    
    
            else:
    
                print(
                    f"[로그] 직접 작성된 자막 "
                    f"{len(subtitles)}개 사용 완료"
                )
    
    
            # ==================================================
            # 결과 반환
            # ==================================================
    
            return jsonify({
    
                "title":
                    title,
    
                # ★ Flask 5000번 주소를 명시
                "audio": f"http://192.168.0.5:5000/audio/{job_id}.mp3",
    
                "subtitles":
                    subtitles
            })
    
    
        except Exception as e:
    
            print()
            print(
                "[오류] 유튜브 처리 중 문제가 발생했습니다."
            )
    
            print(
                repr(e)
            )
    
    
            return jsonify({
    
                "error":
                    str(e)
    
            }), 500
    
    
    # ==================================================
    # 오디오 파일
    # ==================================================
    
    @app.route("/audio/<filename>")
    def audio(filename):
    
        print(f"[로그] 오디오 요청: {filename}")
    
        filepath = os.path.join(
            DOWNLOAD_DIR,
            filename
        )
    
        print(f"[로그] 오디오 경로: {filepath}")
    
        if not os.path.isfile(filepath):
            print("[오류] 오디오 파일이 존재하지 않습니다.")
            return "Audio Not Found", 404
    
        print("[로그] 오디오 전송")
    
        return send_from_directory(
            DOWNLOAD_DIR,
            filename
        )
    
    
    # ==================================================
    # 서버 실행
    # ==================================================
    
    if __name__ == "__main__":
    
        print()
        print(
            "[로그] 서버 시작"
        )
    
        print(
            "[로그] http://127.0.0.1:8000"
        )
    
        print()
    
    
        try:
    
            app.run(
                host="0.0.0.0",
                port=5000,
                debug=False
            )
    
    
        except Exception as e:
    
            print()
            print(
                "=============================="
            )
    
            print(
                "서버 오류"
            )
    
            print(
                "=============================="
            )
    
            print(
                repr(e)
            )
    
            print()
    
            input(
                "엔터를 누르면 종료됩니다..."
            )