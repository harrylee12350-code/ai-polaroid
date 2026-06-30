import os
from flask import Flask, request
import worker

app = Flask(__name__)

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
        .file-upload-box { border: 2px dashed #ced4da; padding: 30px; text-align: center; border-radius: 10px; background: #f8f9fa; cursor: pointer; margin-top: 5px; transition: 0.3s; }
        .submit-btn { width: 100%; padding: 16px; background: #ffffff; border: 1px solid #ced4da; border-radius: 10px; font-size: 1.1em; font-weight: bold; cursor: pointer; margin-top: 10px; }
    </style>
    <script>
        // 모드 전환에 따라 입력창을 바꾸는 자바스크립트 마법사
        function toggleMode() {
            const mode = document.querySelector('input[name="mode"]:checked').value;
            const normalFields = document.getElementById('normal-fields');
            const babyFields = document.getElementById('baby-fields');
            const normalTitle = document.getElementById('normal_title');
            const ageInput = document.getElementById('age');

            if (mode === 'normal') {
                normalFields.style.display = 'block';
                babyFields.style.display = 'none';
                normalTitle.required = true;
                ageInput.required = false;
            } else {
                normalFields.style.display = 'none';
                babyFields.style.display = 'block';
                normalTitle.required = false;
                ageInput.required = true;
            }
        }
        window.onload = toggleMode; // 페이지 켜질 때 즉시 실행
    </script>
</head>
<body>
    <div class="container">
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label class="title">서비스 모드를 선택해 주세요</label>
                <div class="radio-group">
                    <label><input type="radio" name="mode" value="normal" checked onchange="toggleMode()"> 일반 모드 (상세 기록)</label>
                    <label><input type="radio" name="mode" value="baby" onchange="toggleMode()"> 👶 아기 모드 (성장 기록)</label>
                </div>
            </div>
            <div class="logo-title">🎬 찰나 - 당신의<br>순간을 영화로</div>
            
            <div class="form-group" style="border-bottom: none; padding-bottom: 0;">
                
                <div id="normal-fields">
                    <label class="title" for="normal_title" style="margin-bottom: 5px;">영상 제목</label>
                    <input type="text" id="normal_title" name="normal_title" class="form-control" placeholder="예: 2026년 여름 제주도" style="margin-bottom: 20px;">
                    <label class="title" for="normal_memo" style="margin-bottom: 5px;">기억할 메모</label>
                    <input type="text" id="normal_memo" name="normal_memo" class="form-control" placeholder="예: 우리들의 완벽했던 하루" style="margin-bottom: 20px;">
                </div>

                <div id="baby-fields" style="display: none;">
                    <label class="title" for="age" style="margin-bottom: 5px;">아이 연령</label>
                    <input type="text" id="age" name="age" class="form-control" placeholder="예: 1년 7개월" style="margin-bottom: 20px;">
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
                </div>
                
                <label class="title">사진 2~5장 업로드</label>
                <div class="file-upload-box" onclick="document.getElementById('photos').click()">
                    <span id="upload-text" style="font-size: 1.2em; display: block; margin-bottom: 8px; font-weight: bold;">↑ Upload</span>
                    <span id="upload-subtext" style="color: #6c757d; font-size: 0.85em;">200MB per file • JPG, PNG</span>
                </div>
                <input type="file" id="photos" name="photos" multiple accept="image/*" style="display: none;" required 
                       onchange="document.getElementById('upload-text').innerText = this.files.length + '장의 사진이 선택되었습니다 ✅'; 
                                 document.getElementById('upload-text').style.color = '#27ae60';
                                 document.getElementById('upload-subtext').innerText = '이제 아래 시작 버튼을 눌러주세요!';">
            </div>
            <button type="submit" class="submit-btn">🚀 찰나 영화 인화 시작</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return INDEX_HTML

@app.route('/upload', methods=['POST'])
def upload():
    # 프론트엔드에서 넘어오는 모든 정보(모드 포함)를 싹 수집합니다
    mode = request.form.get('mode', 'normal')
    normal_title = request.form.get('normal_title', '')
    normal_memo = request.form.get('normal_memo', '')
    age = request.form.get('age', '')
    height = request.form.get('height', '')
    weight = request.form.get('weight', '')
    photos = request.files.getlist('photos')

    # worker.py로 모든 정보를 넘겨줍니다
    final_result_html = worker.process_video_and_render(mode, normal_title, normal_memo, age, height, weight, photos)
    
    return final_result_html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)