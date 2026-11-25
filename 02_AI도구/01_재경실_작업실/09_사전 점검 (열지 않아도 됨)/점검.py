# -*- coding: utf-8 -*-
"""교육 전 사전 점검 — 재경실_작업실의 "00_사전 점검.bat"이 부른다.

실습 폴더는 건드리지 않는다. 작업실 파일이 다 있는지(파일목록.txt)와 들어 있는 python.exe가 실행되는지 본다.
결과는 화면과 "사전 점검 결과.txt"(재경실_작업실 바로 아래)에 남긴다.
--gui 를 붙이면 점검 창(Ready-Check.ps1)이 읽는 줄(@@ JSON)을 함께 찍는다. 약속 = 교안-세트 skill assets/사전점검_GUI/README.md
"""
import re
import base64
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                                        # -I 로 돌아도 같은 폴더의 공통점검.py 를 찾게
import 공통점검 as common                                             # 교안-세트 skill 틀 그대로 (고치지 않음)

ROOT = HERE.parent                                                   # 재경실_작업실
DOC, TRIP = ROOT / "01_품의서", ROOT / "02_출장복명"
PROG = DOC / "09_프로그램 (열지 않아도 됨)"
TRIP_PROG = TRIP / "09_프로그램 (열지 않아도 됨)"
PY_DOC = PROG / "python" / "python.exe"
PY_TRIP = TRIP_PROG / "python" / "python.exe"
NO_WINDOW = 0x08000000
APP_URL = "https://chatgpt.com/download"   # ChatGPT 공식 내려받기 페이지 (Windows 데스크탑 앱)

lines, fails, warns = [], [], []
PLACE_NOTE = []
GUI = "--gui" in sys.argv[1:]
# 점검 창의 항목 key (준비점검_설정.json 항목과 같다). 제목 앞부분으로 고른다
KEYS = [("압축", "place"), ("폴더 위치", "place"), ("출장복명 skill", "skill"), ("ChatGPT 로그인", "login"),
        ("ChatGPT", "app")]


def gui(**m):
    if GUI:
        print("@@ " + json.dumps(m, ensure_ascii=False), flush=True)


def say(ok, title, detail="", fix="", link=None):
    """link = (보일 글자, 주소). 점검 창은 그 줄 오른쪽에 누르면 열리는 링크로, 결과 파일은 주소 한 줄로 남긴다"""
    mark = {True: "통과", False: "실패", None: "확인"}[ok]
    out = [f"[{mark}] {title}" + (f" — {detail}" if detail else "")]
    if fix:
        out.append(f"        → {fix}")
    if link:
        out.append(f"        → 주소 : {link[1]}")
    lines.extend(out)
    (fails if ok is False else warns if ok is None else []).append(title)
    for l in out:
        print(l, flush=True)
    key = next((k for w, k in KEYS if title.startswith(w)), title)
    extra = {"link": {"text": link[0], "url": link[1]}} if link else {}
    gui(key=key, s={True: "ok", False: "no", None: "warn"}[ok], d=detail, fix=fix, **extra)


def check_place():
    p = str(ROOT).lower()
    if "\\temp\\" in p or "\\appdata\\local\\temp" in p or ".zip" in p:
        say(False, "압축 풀기", f"압축 파일 안에서 실행됨 ({ROOT})",
            "zip 파일을 마우스 오른쪽 → “압축 풀기”로 바탕화면에 푼 뒤, 푼 폴더에서 다시 실행하세요")
        return False
    longest = max((len(str(f)) for f in ROOT.rglob("*")), default=0)
    if longest > 240:
        say(False, "폴더 위치", f"경로가 너무 깁니다 (가장 긴 경로 {longest}자)",
            "재경실_작업실 폴더를 바탕화면이나 C:\\ 바로 아래로 옮기세요")
        return False
    note = " · OneDrive 폴더 안" if "onedrive" in p else ""
    PLACE_NOTE.append(f"{ROOT}{note}")
    return True


def check_files():
    """zip 을 만들 때 적어 둔 파일목록.txt 와 비교한다 (공통점검.py). 목록이 없으면 프로그램 실행만 본다"""
    miss, has_list = common.missing_files(ROOT, HERE)
    if miss:
        more = f" 외 {len(miss) - 5}개" if len(miss) > 5 else ""
        say(False, "압축 풀기 · 실습 파일", "빠진 파일 : " + ", ".join(miss[:5]) + more,
            "처음 받은 zip을 다시 풀어 주세요. 백신이 python.exe를 지웠다면 보조강사에게 알려 주세요")
        return False
    if not (PY_DOC.exists() and PY_TRIP.exists()):
        say(False, "압축 풀기 · 실습 파일", "실습 프로그램 폴더가 없음", "처음 받은 zip을 다시 풀어 주세요")
        return False
    for py in (PY_DOC, PY_TRIP):
        try:
            r = run([py, "-I", "-B", "-c", "print('ok')"], ROOT, timeout=60)
            ok = r.returncode == 0 and "ok" in r.stdout
        except Exception:
            ok = False
        if not ok:
            say(False, "압축 풀기 · 실습 프로그램", f"{py.relative_to(ROOT)} 이 실행되지 않음",
                "회사 보안 프로그램이 python.exe 실행을 막았을 수 있습니다. 보조강사에게 알려 주세요")
            return False
    say(True, "압축 풀기 · 폴더 위치", PLACE_NOTE[0] + (" · 실습 파일" if has_list else "") + " · 프로그램 실행 확인")
    return True


def run(args, cwd, env=None, timeout=300):
    return subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, env=env, creationflags=NO_WINDOW)




def check_app():
    """앱 본체 패키지(예: OpenAI.Codex)가 정상 상태로 있을 때만 설치됨으로 본다.
    앱을 지워도 남는 OpenAI.CodexPrimaryRuntime.* (런타임)는 세지 않는다"""
    try:
        r = run(["powershell", "-NoProfile", "-Command",
                 "Get-AppxPackage | Where-Object { ($_.Name -like 'OpenAI.*' -or $_.Name -like '*ChatGPT*') "
                 "-and $_.Name -notlike '*Runtime*' -and $_.Status -eq 'Ok' } | "
                 "Select-Object -ExpandProperty Name"], ROOT, timeout=60)
        names = [n for n in r.stdout.split() if n]
    except Exception:
        names = []
    exe = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ChatGPT" / "ChatGPT.exe"
    if names or exe.exists():
        say(True, "ChatGPT 데스크탑 앱", "설치됨. 폴더 열기는 사전 안내 3번대로 확인")
        return True
    say(None, "ChatGPT 데스크탑 앱", "설치를 찾지 못함",
        "“설치 페이지 열기” → ChatGPT Installer.exe 실행 → Microsoft Store 창에서 설치 → 로그인",
        link=("설치 페이지 열기", APP_URL))
    return False


def check_login(app_ok):
    """앱(안의 Codex)이 로그인하면 %USERPROFILE%\\.codex\\auth.json 에 로그인 정보를 둔다.
    이 파일은 앱을 지워도 남으므로 앱이 있을 때만 본다.
    토큰 · 이메일은 읽어서 출력하지 않고, 로그인 방식과 요금제 이름만 본다"""
    if not app_ok:
        say(None, "ChatGPT 로그인", "앱이 없어 확인하지 않음",
            "ChatGPT 데스크탑 앱을 설치하고 교육용 계정으로 로그인한 뒤 다시 점검하세요")
        return
    auth = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "auth.json"
    fix = "ChatGPT 데스크탑 앱을 열어 교육용 계정으로 로그인한 뒤 다시 점검하세요"
    try:
        d = json.loads(auth.read_text(encoding="utf-8"))
    except Exception:
        say(None, "ChatGPT 로그인", "로그인 기록을 찾지 못함", fix)
        return
    tok = d.get("tokens") or {}
    if d.get("auth_mode") != "chatgpt" or not tok.get("refresh_token"):
        say(None, "ChatGPT 로그인", "ChatGPT 계정으로 로그인되어 있지 않음", fix)
        return
    plan = ""
    try:
        part = tok["id_token"].split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
        plan = (claims.get("https://api.openai.com/auth") or {}).get("chatgpt_plan_type") or ""
    except Exception:
        pass
    say(True, "ChatGPT 로그인", "로그인됨" + (f" (요금제 : {plan})" if plan else ""))




def other_trip_skills(skills):
    """trip-report 말고 이름이나 설명에 출장 · 복명 · trip 이 든 skill (예전 실습에서 남은 것). 지우지 않고 알리기만 한다"""
    found = []
    try:
        for d in sorted(skills.iterdir()):
            if not d.is_dir() or d.name == "trip-report":
                continue
            head = ""
            try:
                head = (d / "SKILL.md").read_text(encoding="utf-8", errors="ignore")[:600]
            except Exception:
                pass
            if re.search(r"trip|출장|복명", d.name + " " + head, re.I):
                found.append(d.name)
    except Exception:
        pass
    return found


def new_skill_names():
    try:
        return json.loads((HERE / "준비점검_설정.json").read_text(encoding="utf-8")).get("새로_설치할_skill") or []
    except Exception:
        return []


def check_skill():
    """과제 2에서 출장복명 skill을 새로 설치하므로, 예전에 설치한 trip-report 는 지우지 않고 백업 폴더로 옮긴다 (공통점검.py).
    다른 출장복명 skill 은 알리기만 한다"""
    skills = common.codex_home() / "skills"
    moved = common.move_old_skills(new_skill_names())
    failed = [n for n, d in moved if d is None]
    if failed:
        say(False, "출장복명 skill 정리", f"예전에 설치한 skill을 옮기지 못함 ({', '.join(failed)})",
            "ChatGPT 앱을 닫고 다시 점검하세요")
        return
    if moved:
        msg = f"예전에 설치한 출장복명 skill을 백업 폴더로 옮겼습니다 ({moved[0][1].parent}). 과제 2에서 새로 설치합니다"
    else:
        msg = "설치된 출장복명 skill 없음. 과제 2에서 새로 설치합니다"
    others = other_trip_skills(skills) if skills.exists() else []
    if others:
        say(None, "출장복명 skill 정리", f"다른 출장복명 skill이 설치되어 있음 ({', '.join(others)})",
            "과제 2에서 AI가 이 skill을 대신 쓸 수 있습니다")
    else:
        say(True, "출장복명 skill 정리", msg)


def main():
    print("\n  재경실 워크샵 사전 점검을 시작합니다 (실습 폴더는 바꾸지 않습니다).\n", flush=True)
    check_place() and check_files()
    check_login(check_app())
    check_skill()
    if fails:
        tail = f"실패 {len(fails)}개 : " + ", ".join(fails)
    elif warns:
        tail = "실습 파일은 준비됐습니다. “확인” 항목만 안내대로 해 주세요."
    else:
        tail = "모두 통과했습니다."
    out = ["재경실 워크샵 사전 점검 결과", f"점검 시각 : {datetime.datetime.now():%Y-%m-%d %H:%M}", f"PC : {os.environ.get('COMPUTERNAME', '')}", ""] + lines + ["", tail]
    try:
        g = json.loads((Path(__file__).parent / "준비점검_설정.json").read_text(encoding="utf-8")).get("교안") or {}
        if g.get("주소"):
            out += ["", f"교안 : {g.get('이름', '')} {g['주소']}".replace("  ", " ")]
    except Exception:
        pass
    try:
        (ROOT / "사전 점검 결과.txt").write_text("\r\n".join(out) + "\r\n", encoding="utf-8-sig", newline="")
        saved = "  결과를 “사전 점검 결과.txt”에 저장했습니다."
    except Exception:
        saved = ""
    gui(done=True, tail=tail.replace("\n  → ", "\n→ "), result="사전 점검 결과.txt" if saved else "")
    print("\n  " + tail + "\n" + saved + "\n")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
