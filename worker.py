import os
import uuid
from PIL import Image, ImageOps
from moviepy.editor import ImageSequenceClip

def process_video_and_render(mode, normal_title, normal_memo, age, height, weight, photos):
    # 🚨 [백엔드 안전장치] 비정상적인 접근으로 1장만 넘어왔을 경우 서버에서 강제 반환
    valid_photos = [photo for photo in photos if photo.filename != '']
    if len(valid_photos) < 2:
        return """
        <script>
            alert("서버 오류: 최소 2장 이상의 사진이 필요합니다. 뒤로가기를 눌러 다시 선택해 주세요.");
            history.back();
        </script>
        """

    # =================================================================
    # 🎬 [1단계] 실전 영상 렌더링 엔진 
    # =================================================================
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    temp_dir = f"temp_{uuid.uuid4().hex}"
    os.makedirs(temp_dir)
    
    image_paths = []
    target_size = (720, 1280) 
    
    for i, photo in enumerate(valid_photos):
        try:
            img = Image.open(photo)
            img = ImageOps.exif_transpose(img)
            img = img.convert('RGB')
            img_resized = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
            
            temp_path = os.path.join(temp_dir, f"img_{i}.jpg")
            img_resized.save(temp_path)
            image_paths.append(temp_path)
        except Exception as e:
            print(f"이미지 처리 오류: {e}")
            continue

    if image_paths:
        clip = ImageSequenceClip(image_paths, fps=0.5)
        video_filename = f"chalna_{uuid.uuid4().hex[:8]}.mp4"
        video_path = os.path.join(static_dir, video_filename)
        
        clip.write_videofile(video_path, fps=24, codec='libx264', preset='ultrafast', logger=None)
        
        for p in image_paths:
            try: os.remove(p)
            except: pass
        try: os.rmdir(temp_dir)
        except: pass
            
        video_url = f"/{video_path}"
    else:
        video_url = ""

    # =================================================================
    # 📝 [2단계] 모드별 텍스트 출력
    # =================================================================
    if mode == 'baby':
        title_text = f"[ {age}의 성장 기록 ]" if age else "[ 아기 성장 기록 ]"
        if height or weight:
            h = height if height else "?"
            w = weight if weight else "?"
            sub_text = f"{h}cm / {w}kg"
        else:
            sub_text = "오늘도 쑥쑥 자라고 있어요!"
    else:
        title_text = f"[ {normal_title} ]" if normal_title else "[ 찰나의 순간 ]"
        sub_text = normal_memo if normal_memo else "소중한 기억을 영화로 기록합니다"

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
                <div class="age-text">{title_text}</div>
                <div class="growth-data">{sub_text}</div>
            </div>
            <a href="{video_url}" download="chalna_movie.mp4" style="text-decoration: none;">
                <button class="save-btn">💾 내 폰에 영화 저장하기</button>
            </a>
        </div>
    </body>
    </html>
    """
    
    return RESULT_HTML