from flask import Flask, render_template, request, redirect, url_for
import json
import os
import tempfile, shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

# -----------------------------
# 1) 멤버 데이터 읽기
# -----------------------------
DATA_FILE = os.path.join(app.root_path, "data", "members.json")

def load_members():
    """members.json에서 members 리스트 가져오기"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["members"]   

def get_member_by_username(username):
    """github_username으로 특정 멤버 한 명 찾기"""
    members = load_members()
    for m in members:
        if m.get("github_username") == username:
            return m
    return None

def save_members(members):
    """members 리스트를 members.json에 안전하게 저장"""
    dirpath = os.path.dirname(DATA_FILE)
    os.makedirs(dirpath, exist_ok=True)
    payload = {"members": members}

    # 임시 파일에 먼저 쓰고 교체 (부분 손상 방지)
    fd, tmp = tempfile.mkstemp(dir=dirpath, suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        shutil.move(tmp, DATA_FILE)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "files")
ALLOWED_EXTS = {"pdf", "png", "jpg", "jpeg", "zip", "pptx"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
# 파일 업로드
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS

# -----------------------------
# 2) 라우트 설정
# -----------------------------

# 메인 페이지 (Team)
@app.route("/")
def index():
    members = load_members()
    return render_template("index.html", members=members)

# 멤버 목록 페이지 (Member)
@app.route("/result")
def result():
    members = load_members()
    return render_template("result.html", members=members)
# /member 로 들어와도 /result 로 보내기
@app.route("/member")
def member_redirect():
    return redirect(url_for("result"))


# 멤버 상세 페이지: /result/<username>
@app.route("/result/<username>")
def member_detail(username):
    member = get_member_by_username(username)
    if member is None:
        return "Member not found", 404
    return render_template("member_detail.html", member=member)

# 멤버 수정 페이지: /input?username=...
@app.route("/input")
def input_page():
    username = request.args.get("username")
    member = get_member_by_username(username) if username else None
    return render_template("input.html", member=member)

# 멤버 정보 업데이트 페이지
@app.route("/member/update", methods=["POST"])
def update_member():
    username = request.form.get("github_username")  # hidden으로 실사용 식별자 전달
    if not username:
        return "github_username is required", 400

    members = load_members()
    # 대상 멤버 찾기
    target = None
    for m in members:
        if m.get("github_username") == username:
            target = m
            break
    if not target:
        return "Member not found", 404

    # 단일 필드 업데이트
    target["name"] = (request.form.get("name") or "").strip()
    target["english_name"] = (request.form.get("english_name") or "").strip()
    target["intro"] = (request.form.get("intro") or "").strip()
    target["phone"] = (request.form.get("phone") or "").strip()
    target["email"] = (request.form.get("email") or "").strip()
    target["portfolio_link"] = (request.form.get("portfolio_link") or "").strip()
    target["portfolio_file"] = (request.form.get("portfolio_file") or "").strip()
    auto_profile_url = f"https://github.com/{username}"
    target["github_profile"] = auto_profile_url

    # ✅ 다중 입력 필드(role[], major[]) 처리
    roles = [r.strip() for r in request.form.getlist("role[]") if r.strip()]
    majors = [m.strip() for m in request.form.getlist("major[]") if m.strip()]
    # 만약 input 이름이 role / major 단일로 왔다면 fallback
    if not roles and request.form.get("role"):
        roles = [x.strip() for x in request.form.get("role", "").split(",") if x.strip()]
    if not majors and request.form.get("major"):
        majors = [x.strip() for x in request.form.get("major", "").split(",") if x.strip()]

    target["role"] = roles if roles else target.get("role", [])
    target["major"] = majors if majors else target.get("major", [])

    # ✅ 파일 업로드 처리
    old_file = (request.form.get("portfolio_file_old") or "").strip()
    remove_flag = request.form.get("remove_portfolio_file") == "1"
    file = request.files.get("portfolio_upload")
    if remove_flag and old_file:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], old_file))
        except Exception:
            pass
        target["portfolio_file"] = ""

    # 🔸 새 파일 업로드된 경우 (교체)
    elif file and file.filename:
        if not allowed_file(file.filename):
            return "허용되지 않는 파일 형식입니다.", 400

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        base = secure_filename(file.filename)

        save_name = base
        i = 1
        while os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], save_name)):
            name, ext = os.path.splitext(base)
            save_name = f"{name}_{i}{ext}"
            i += 1

        file.save(os.path.join(app.config["UPLOAD_FOLDER"], save_name))

        # 기존 파일 있으면 정리(선택)
        if old_file:
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], old_file))
            except Exception:
                pass

        target["portfolio_file"] = save_name

    # ✅ 포트폴리오 항목들 (다중)
    titles = request.form.getlist("project_title[]")
    periods = request.form.getlist("period[]")      
    proles  = request.form.getlist("proj_role[]")
    descs   = request.form.getlist("description[]")

    portfolio = []
    for i in range(max(len(titles), len(periods), len(proles), len(descs))):
      t = (titles[i] if i < len(titles) else "").strip()
      prd = (periods[i] if i < len(periods) else "").strip()
      rl = (proles[i] if i < len(proles) else "").strip()
      ds = (descs[i] if i < len(descs) else "").strip()
      if any([t, prd, rl, ds]):   
          portfolio.append({
              "project_title": t,
              "period": prd,
              "role": rl,
              "description": ds
          })

    target["portfolio"] = portfolio

    # 저장
    save_members(members)

    # 완료 후 상세 페이지로
    return redirect(url_for("member_detail", username=username))

# 비상 연락망 페이지
@app.route("/contact")
def contact():
    members = load_members()
    return render_template("contact.html", members=members)


# -----------------------------
# 3) 앱 실행
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)