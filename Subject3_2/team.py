from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
import uuid

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 데이터 파일 경로 설정 및 디렉토리 생성
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "members.json")
os.makedirs(DATA_DIR, exist_ok=True)


# ----------------------------------------------------
# 💾 데이터 관리 함수 (JSON 구조 반영)
# ----------------------------------------------------

def load_members():
    """members.json 파일을 읽어 'members' 리스트를 반환합니다."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 최상위 키 "members"를 확인하고 리스트를 반환합니다.
            return data.get("members", [])
    except (json.JSONDecodeError, AttributeError):
        return []

def save_members(members):
    """팀원 리스트를 members.json 파일에 {"members": [...]} 형태로 저장합니다."""
    data = {"members": members}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------
# 🌐 라우트 정의 (페이지 연결 및 플로우 처리)
# ----------------------------------------------------

# 🔸 1. 홈 페이지
@app.route('/')
def index():
    members = load_members()  
    return render_template('index.html', members=members)

# 🔸 2. 팀원 입력/수정 페이지 (C: Create, U: Update)
@app.route('/input', methods=['GET', 'POST'])
def input_member():
    members = load_members()

    if request.method == 'POST':
        # JSON 구조에 맞춘 모든 필드를 가져옵니다.
        name = request.form.get('name')
        english_name = request.form.get('english_name')
        intro = request.form.get('intro')
        role = request.form.get('role')
        major = request.form.get('major')
        phone = request.form.get('phone') 
        email = request.form.get('email')
        github_username = request.form.get('github_username')
        github_profile = request.form.get('github_profile')
        portfolio_link = request.form.get('portfolio_link')
        member_id = request.form.get('id')

        # 공통 데이터 딕셔너리 구성 (입력 폼에서 받는 데이터)
        member_data = {
            "name": name,
            "english_name": english_name,
            "intro": intro,
            "role": role,
            "major": major,
            "phone": phone,
            "email": email,
            "github_username": github_username,
            "github_profile": github_profile,
            "portfolio_link": portfolio_link,
        }

        if member_id:  # 수정 모드
            for m in members:
                if m.get('id') == member_id:
                    m.update(member_data)
                    break
        else:  # 신규 추가 모드
            new_member = member_data
            new_member["id"] = str(uuid.uuid4())[:8]
            new_member["portfolio"] = [] # 포트폴리오 리스트 초기화
            members.append(new_member)

        save_members(members)
        return redirect(url_for('show_result'))

    # GET 요청: 수정 모드 데이터 로드
    member_id = request.args.get('id')
    edit_member = None
    if member_id:
        edit_member = next((m for m in members if m.get('id') == member_id), None)
        if not edit_member:
             abort(404)

    return render_template('input.html', member=edit_member)


# 🔸 3. 팀원 목록 페이지 (R: Read - 목록)
@app.route('/result')
def show_result():
    members = load_members()
    return render_template('result.html', members=members)


# 🔸 4. 팀원 상세 페이지 (R: Read - 상세)
@app.route('/result/<id>')
def member_detail(id):
    members = load_members()
    member = next((m for m in members if m.get('id') == id), None)

    if not member:
        abort(404)
        
    # 포트폴리오 데이터가 없으면 템플릿 에러 방지용 초기화
    member.setdefault("portfolio", []) 
        
    return render_template('member_detail.html', member=member)


# 🔸 5. 연락처 페이지
@app.route('/contact')
def contact_info():
    members = load_members()  
    return render_template('contact.html', members=members)


# ----------------------------------------------------
# 🚀 애플리케이션 실행
# ----------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)