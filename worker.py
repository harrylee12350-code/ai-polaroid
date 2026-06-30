import os
import uuid
from PIL import Image, ImageOps
from moviepy.editor import ImageSequenceClip

def process_video_and_render(age, height, weight, photos):
    # =================================================================
    # 🎬 [1단계] 실전 영상 렌더링 엔진 (사진 합성 및 mp4 제작)
    # =================================================================
    
    # 웹에서 영상을 보여주기 위한 폴더 세팅
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    # 사진 크기를 균일하게 맞추기 위한 임시 작업장 생성 (고유번호 부여)
    temp_dir = f"temp_{uuid.uuid4().hex}"
    os.makedirs(temp_dir)
    
    image_paths = []
    # 스마트폰 세로 꽉 차는 사이즈 (Reels/Shorts 최적화 비율)
    target_size = (720, 1280) 
    
    # 1-1. 부모님이 올린 사진들을 하나씩 꺼내서 예쁘게 다듬기
    for i, photo in enumerate(photos):
        if photo.filename == '':
            continue
        try:
            # 사진을 열어서 스마트폰 화면에 딱 맞게 자르고 크기 조절
            img = Image.open(photo)
            img = img.convert('RGB')
            img_resized = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
            
            # 임시 폴더에 저장
            temp_path = os.path.join(temp_dir, f"img_{i}.jpg")
            img_resized.save(temp_path)
            image_paths.append(temp_path)
        except Exception as e:
            print(f"이미지 처리 오류: {e}")
            continue

    # 1-2. 다듬어진 사진들을 이어 붙여서 하나의 영화(mp4)로 만들기
    if image_paths:
        # 사진 1장당 2초씩 재생 (fps=0.5 -> 5장이면 총 10초 영상)
        clip = ImageSequenceClip(image_paths, fps=0.5)
        
        # 캐시 충돌 방지를 위해 영상 파일명에 고유 난수 부여
        video_filename = f"chalna_{uuid.uuid4().hex[:8]}.mp4"
        video_path = os.path.join(static_dir, video_filename)
        
        # 레일웨이 서버 과부하를 막기 위해 초고속(ultrafast) 렌더링 옵션 적용
        clip.write_videofile(video_path, fps=24, codec='libx264', preset='ultrafast', logger=None)
        
        # 임시로 썼던 사진과 폴더는 서버 용량 확보를 위해 즉시 삭제 (청소)
        for p in image_paths:
            try: os.remove(p)
            except: pass
        try: os.rmdir(temp_dir)
        except: pass
            
        # HTML에 띄워줄 최종 영상 주소
        video_url = f"/{video_path}"
    else:
        # 혹시라도 사진 처리에 실패했을 경우를 대비한 안전망
        video_url = ""

    # =================================================================
    # 📝 [2단계] 결과 화면(HTML) 조립 및 출력
    # =================================================================
    if height or weight:
        height_str = height if height else "?"
        weight_str = weight if weight else "?"
        growth_text = f"{height_str}cm / {weight_str}kg"
    else:
        growth_text = "오늘도 쑥쑥 자라고 있어요!"

    # 완성된 영상 URL과 입력된 데이터를 HTML에 꽂아 넣습니다.
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
            .video-placeholder {{ width: 100%; background: #000; border-radius: 12px; margin-bottom: 20px; overflow: hidden; display: flex; justify-content: center; align-items: center; }}
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
                <div class="age-text">[ {age}의 성장 기록 ]</div>
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