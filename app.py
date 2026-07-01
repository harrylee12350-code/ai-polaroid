import os
from flask import Flask, request
import worker

app = Flask(__name__)

# =====================================================================
# 1. 기존 메인 화면 (B2C 일반 부모님용 - 화이트 테마)
# =====================================================================
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
        function handleFileSelect(input) {
            const count = input.files.length;
            const text = document.getElementById('upload-text');
            const subtext = document.getElementById('upload-subtext');
            if (count === 0) return;
            if (count < 2) {
                text.innerText = '1장만 선택됨 (최소 2장 필요) ⚠️';
                text.style.color = '#e74c3c';
                subtext.innerText = '카메라 촬영 대신 갤러리에서 여러 장을 선택해 주세요!';
            } else if (count > 5) {
                text.innerText = count + '장 선택됨 (최대 5장) ⚠️';
                text.style.color = '#e74c3c';
                subtext.innerText = '사진을 5장 이하로 줄여주세요.';
            } else {
                text.innerText = count + '장의 사진이 선택되었습니다 ✅';
                text.style.color = '#27ae60';
                subtext.innerText = '이제 아래 시작 버튼을 눌러주세요!';
            }
        }
        function validateForm() {
            const fileInput = document.getElementById('photos');
            if (fileInput.files.length < 2) {
                alert("사진은 최소 2장 이상 선택해야 합니다.");
                return false;
            }
            if (fileInput.files.length > 5) {
                alert("사진은 최대 5장까지만 인화할 수 있습니다.");
                return false;
            }
            return true;
        }
        window.onload = toggleMode;
    </script>
</head>
<body>
    <div class="container">
        <form action="/upload" method="POST" enctype="multipart/form-data" onsubmit="return validateForm()">
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
                <label class="title">사진 2~5장 업로드 (갤러리 선택)</label>
                <div class="file-upload-box" onclick="document.getElementById('photos').click()">
                    <span id="upload-text" style="font-size: 1.2em; display: block; margin-bottom: 8px; font-weight: bold;">↑ Upload</span>
                    <span id="upload-subtext" style="color: #6c757d; font-size: 0.85em;">갤러리에서 여러 장을 선택하세요</span>
                </div>
                <input type="file" id="photos" name="photos" multiple accept="image/*" style="display: none;" required onchange="handleFileSelect(this)">
            </div>
            <button type="submit" class="submit-btn">🚀 찰나 영화 인화 시작</button>
        </form>
    </div>
</body>
</html>
"""

# =====================================================================
# 2. VIP 영업용 화면 (B2B/팬덤 특화 - 블랙&골드 프리미엄 테마)
# =====================================================================
VIP_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIP 전용 찰나</title>
    <style>
        /* 프리미엄 블랙 & 골드 테마 */
        body { font-family: -apple-system, sans-serif; background: #121212; margin: 0; padding: 20px; color: #f8f9fa; }
        .container { max-width: 500px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(212, 175, 55, 0.15); border: 1px solid #333; }
        .logo-title { font-size: 2.2em; font-weight: 900; margin-bottom: 5px; color: #D4AF37; text-align: center; letter-spacing: 1px; }
        .sub-title { text-align: center; color: #aaaaaa; margin-bottom: 30px; font-size: 0.95em; }
        .form-group { margin-bottom: 25px; }
        .form-group label.title { display: block; font-weight: bold; margin-bottom: 10px; color: #e0e0e0; font-size: 1.05em; }
        .form-control { width: 100%; padding: 14px; background: #2c2c2c; border: 1px solid #444; border-radius: 10px; color: #fff; box-sizing: border-box; font-size: 1em; margin-top: 5px; transition: 0.3s; }
        .form-control:focus { border-color: #D4AF37; outline: none; }
        .file-upload-box { border: 2px dashed #D4AF37; padding: 30px; text-align: center; border-radius: 10px; background: rgba(212, 175, 55, 0.05); cursor: pointer; margin-top: 5px; transition: 0.3s; }
        .file-upload-box:hover { background: rgba(212, 175, 55, 0.1); }
        .submit-btn { width: 100%; padding: 16px; background: linear-gradient(135deg, #D4AF37, #AA8A2A); border: none; border-radius: 10px; font-size: 1.2em; font-weight: bold; color: #121212; cursor: pointer; margin-top: 15px; transition: 0.3s; }
        .submit-btn:hover { box-shadow: 0 0 15px rgba(212, 175, 55, 0.4); transform: translateY(-2px); }
    </style>
    <script>
        function handleFileSelectVIP(input) {
            const count = input.files.length;
            const text = document.getElementById('upload-text-vip');
            const subtext = document.getElementById('upload-subtext-vip');
            if (count === 0) return;
            if (count < 2) {
                text.innerText = '1장만 선택됨 (최소 2장 필요) ⚠️';
                text.style.color = '#e74c3c';
                subtext.innerText = '갤러리에서 여러 장을 선택해 주세요.';
            } else if (count > 5) {
                text.innerText = count + '장 선택됨 (최대 5장) ⚠️';
                text.style.color = '#e74c3c';
                subtext.innerText = '사진을 5장 이하로 줄여주세요.';
            } else {
                text.innerText = count + '장의 사진이 선택되었습니다 👑';
                text.style.color = '#D4AF37';
                subtext.innerText = '아래 제작 버튼을 눌러주세요!';
            }
        }
        function validateFormVIP() {
            const fileInput = document.getElementById('photos_vip');
            if (fileInput.files.length < 2 || fileInput.files.length > 5) {
                alert("사진은 2장~5장 사이로 선택해 주십시오.");
                return false;
            }
            return true;
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="logo-title">VIP CHALNA</div>
        <div class="sub-title">아티스트와 팬을 잇는 특별한 프라이빗 영화관</div>
        
        <form action="/upload" method="POST" enctype="multipart/form-data" onsubmit="return validateFormVIP()">
            <input type="hidden" name="mode" value="normal">
            
            <div class="form-group">
                <label class="title" for="normal_title">VIP 닉네임 (또는 캠페인명)</label>
                <input type="text" id="normal_title" name="normal_title" class="form-control" placeholder="예: 팬클럽 1기 대표님" required>
            </div>
            
            <div class="form-group">
                <label class="title" for="normal_memo">아티스트에게 남길 메시지</label>
                <input type="text" id="normal_memo" name="normal_memo" class="form-control" placeholder="예: 항상 응원합니다!" required>
            </div>
            
            <div class="form-group">
                <label class="title">프라이빗 포토 업로드 (2~5장)</label>
                <div class="file-upload-box" onclick="document.getElementById('photos_vip').click()">
                    <span id="upload-text-vip" style="font-size: 1.2em; display: block; margin-bottom: 8px; font-weight: bold; color: #D4AF37;">↑ 갤러리 열기</span>
                    <span id="upload-subtext-vip" style="color: #888; font-size: 0.85em;">팬미팅 현장 사진을 선택해 주세요</span>
                </div>
                <input type="file" id="photos_vip" name="photos" multiple accept="image/*" style="display: none;" required onchange="handleFileSelectVIP(this)">
            </div>
            
            <button type="submit" class="submit-btn">✨ VIP 전용 영상 인화하기</button>
        </form>
    </div>
</body>
</html>
"""

# =====================================================================
# 3. 라우팅 (경로 연결)
# =====================================================================
@app.route('/')
def index():
    return INDEX_HTML # 일반 고객용

@app.route('/vip')
def vip_index():
    return VIP_HTML # 영업/VIP용 데모 페이지

@app.route('/upload', methods=['POST'])
def upload():
    # 어떤 폼(일반/VIP)에서 날아오든 동일한 렌더링 엔진(worker.py)이 처리합니다!
    mode = request.form.get('mode', 'normal')
    normal_title = request.form.get('normal_title', '')
    normal_memo = request.form.get('normal_memo', '')
    age = request.form.get('age', '')
    height = request.form.get('height', '')
    weight = request.form.get('weight', '')
    photos = request.files.getlist('photos')

    final_result_html = worker.process_video_and_render(mode, normal_title, normal_memo, age, height, weight, photos)
    return final_result_html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)