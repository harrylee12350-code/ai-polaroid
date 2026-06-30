import time

def process_video_and_render(age, height, weight, photos):
    # 1. 기존 5.10.20 영상 제작 로직 (임시 10초 대기 시뮬레이션)
    # 차후 대표님의 진짜 렌더링 코드를 이 자리에 얹습니다.
    # time.sleep(10) 
    video_url = "/static/chalna_movie.mp4" # 완성된 영상 저장 경로 예시

    # 2. 키/체중 유무에 따른 동적 텍스트 생성
    if height or weight:
        height_str = height if height else "?"
        weight_str = weight if weight else "?"
        growth_text = f"{height_str}cm / {weight_str}kg"
    else:
        growth_text = "오늘도 쑥쑥 자라고 있어요!"

    # 3. [프론트엔드] 결과 화면 HTML (worker.py 내장)
    RESULT_HTML = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>찰나 영화 완성</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
            .container {{ max-width: 450px; width: 100%; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .video-placeholder {{ width: 100%; background: #000; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }}
            .video-placeholder video {{ width: 100%; max-height: 60vh; object-fit: contain; }}
            .record-box {{ margin-bottom: 25px; padding: 15px; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #27ae60; }}
            .age-text {{ color: #2c3e50; font-size: 1.1em; font-weight: bold; margin-bottom: 5px; }}
            .growth-data {{ color: #27ae60; font-size: 1.3em; font-weight: 900; }}
            .save-btn {{ width: 100%; padding: 16px; background: #fff; border: 1px solid #ced4da; border-radius: 12px; font-size: 1.1em; font-weight: bold; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="video-placeholder">
                <video src="{video_url}" controls autoplay playsinline></video>
            </div>
            <div class="record-box">
                <div class="age-text">[ {age} 의 성장 기록 ]</div>
                <div class="growth-data">{growth_text}</div>
            </div>
            <a href="{video_url}" download="chalna_movie.mp4" style="text-decoration: none;">
                <button class="save-btn">💾 내 폰에 영화 저장하기</button>
            </a>
        </div>
    </body>
    </html>
    """
    
    return RESULT_HTML