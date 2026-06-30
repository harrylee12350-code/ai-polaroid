import os
from flask import Flask, request
import worker # worker.py 엔진 불러오기

app = Flask(__name__)

# [프론트엔드] 입력 화면 HTML (app.py 내장)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chalna - 찰나 영화 인화</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f8f9fa; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .logo-title { font-size: 2em; font-weight: 900; margin-bottom: 20px; color: #2c3e50; }
        .form-group { margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
        .form-group label.title { display: block; font-weight: bold; margin-bottom: 15px; color: #495057; font-size: 1.05em; }
        .radio-group label { display: block; margin-bottom: 10px; font-size: 1em; cursor: pointer; }
        .form-control { width: 100%; padding: 14px; border: 1px solid #ced4da; border-radius: 10px; box-sizing: border-box; font-size: 1em; margin-top: 5px; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        .file-upload-box { border: 2px dashed #ced4da; padding: 30px; text-align: center; border-radius: 10px; background: #f8f9fa; cursor: pointer; margin-top: 5px; }
        .submit-btn { width: 100%; padding: 16px; background: #ffffff; border: 1px solid #ced4da; border-radius: 10px; font-size: 1.1em; font-weight: bold; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-group">
            <label class="title">서비스 모드를 선택해 주세요</label>
            <div class="radio-group">
                <label><input type="radio" name="mode" value="normal" checked> 일반 모드 (상세 기록)</label>
                <label><input type="radio" name="mode" value="baby"> 👶 아기 모드 (성장 기록)</label>
            </div>
        </div>
        <div class="logo-title">🎬 찰나 - 당신의<br>순간을 영화로</div>
        <form action="/upload" method="POST" enctype="multipart/form-data" style="border-bottom: none;">
            <div class="form-group" style="border-bottom: none; padding-bottom: 0;">
                <label class="title" for="age" style="margin-bottom: 5px;">아이 연령</label>
                <input type="text" id="age" name="age" class="form-control" placeholder="예: 1년 7개월" required style="margin-bottom: 20px;">
                <div class="row" style="margin-bottom: 20px;">
                    <div class="col">
                        <label class="title" for="height">키 (cm)</label>
                        <input type="number" id="height" name="height" class="form-control" placeholder="예: 105" step="0.1">
                    </div>
                    <div class="col">
                        <label class="title" for="weight">체중 (kg)</label>
                        <input type="number" id="weight" name="weight" class="form-control" placeholder="예: 17" step="0.1">
                    </div>
                </div>
                <label class="title">사진 2~5장 업로드</label>
                <div class="file-upload-box" onclick="document.getElementById('photos').click()">
                    <span style="font-size: 1.2em; display: block; margin-bottom: 8px;">↑ Upload</span>
                    <span style="color: #6c757d; font-size: 0.85em;">200MB per file • JPG, PNG</span>
                </div>
                <input type="file" id="photos" name="photos" multiple accept="image/*" style="display: none;" required>
            </div>
            <button type="submit" class="submit-btn">🚀 찰나 영화 인화 시작</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return INDEX_HTML # 입력 화면 송출

@app.route('/upload', methods=['POST'])
def upload():
    # 1. 부모님이 입력한 새로운 데이터 수집
    age = request.form.get('age', '')
    height = request.form.get('height', '')
    weight = request.form.get('weight', '')
    photos = request.files.getlist('photos')

    # 2. worker.py로 데이터 전송 및 완성된 결과 화면(HTML) 응답받기
    final_result_html = worker.process_video_and_render(age, height, weight, photos)
    
    return final_result_html # 완성된 결과 화면 송출

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)