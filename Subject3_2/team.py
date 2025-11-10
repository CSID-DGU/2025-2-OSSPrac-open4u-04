from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

# -----------------------------
# 1) 멤버 데이터 읽기
# -----------------------------
DATA_FILE = os.path.join(app.root_path, "data", "members.json")

def load_members():
    """members.json에서 members 리스트 가져오기"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["members"]   # ★ 중요: 최상단에 "members": [...] 구조

def get_member_by_username(username):
    """github_username으로 특정 멤버 한 명 찾기"""
    members = load_members()
    for m in members:
        if m.get("github_username") == username:
            return m
    return None


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