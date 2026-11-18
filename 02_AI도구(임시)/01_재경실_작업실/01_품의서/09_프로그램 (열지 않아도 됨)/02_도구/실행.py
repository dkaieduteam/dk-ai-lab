# -*- coding: utf-8 -*-
"""품의서 도구 실행기 — 01_품의서 의 「품의서 만들기.bat」 · 「이전 버전으로.bat」이 부른다. AI 는 이 폴더를 고치지 않는다.

    만들기     ① AI작업실의 변환 프로그램이 지금 쓰는 버전과 다르면 : 실행 전 검사 → 시험(시험 기준) → 새 버전으로 적용.
                  다른 품의서(시험 기준)의 모양이 바뀌어도 막지 않고 결과 페이지와 AI작업실의 시험 결과.md 로 알린다.
                  쓰면 안 되는 코드 · 깨진 설정 · 오류 · 멈춤이면 지금 버전을 그대로 쓰고 시험 결과.md
               ② 01_품의서 넣기의 품의서를 HTML 로 → 02_HTML 품의서
               ③ 양식만 남기고 가린 샘플(줄번호 포함) → AI작업실\\샘플
               ④ 결과 페이지(HTML 품의서 확인.html)를 브라우저로 연다
    되돌리기   바로 앞 버전으로 되돌리고 다시 만든다

지키는 것 : 변환은 따로 떨어진 프로세스에서 시간 제한을 두고 돌린다 · 시험한 사본 그대로 적용한다 · 두 번 실행하면 바로 끝낸다 ·
결과 파일은 다 만든 뒤 한 번에 바꿔 넣는다 · 버전을 바꾸다 꺼져도 다음 실행 때 되살린다.
시험용 환경 변수 : 품의서_열지않기 (값이 있으면 브라우저를 열지 않는다)
"""
import ast
import ctypes
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

TOOL = Path(__file__).resolve().parent                  # 02_도구
PROG = TOOL.parent                                      # 09_프로그램 (열지 않아도 됨)
TOP = PROG.parent                                       # 01_품의서
WORK = PROG / "01_품의서 AI작업실"                        # AI 가 고치는 곳
WPROG, SAMPLES = WORK / "프로그램", WORK / "샘플"
BASE = PROG / "03_품의서 자료"                            # AI 가 보지 않는 곳
CUR, PREV, CAND, SWAP, TESTS, LOGS = (BASE / n for n in ("현재", "직전", "후보", "교체중", "시험 기준", "logs"))
IDS, LOCK = BASE / "건목록.tsv", BASE / "실행중.lock"
IN, OUT = TOP / "01_품의서 넣기", TOP / "02_HTML 품의서"
PAGE = OUT / "HTML 품의서 확인.html"
FILES = ("변환.py", "변환설정.json")
SKIP = ("desktop.ini", "thumbs.db")
TEST_TIMEOUT = int(os.environ.get("품의서_시험제한") or 180)     # 초 (시험할 때만 짧게 바꾼다)
FILE_TIMEOUT = int(os.environ.get("품의서_파일제한") or 90)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
FIX_TEST = "시험을 통과하지 못했대. 시험 결과 보고 다시 고쳐 줘."
FIX_NARROW = "다른 품의서 모양도 바뀌었대. 이 품의서에만 맞게 고쳐 줘."
FIX_READ = "변환 오류가 났대. 변환 오류 보고 고쳐 줘."

# 변환 프로그램에 넣으면 안 되는 것 (파일 쓰기 · 다른 프로그램 · 인터넷)
BAD_MODULES = {"os", "subprocess", "socket", "shutil", "tempfile", "ctypes", "urllib", "http", "ftplib", "smtplib", "requests",
               "asyncio", "multiprocessing", "threading", "importlib", "builtins", "winreg", "msvcrt", "signal", "webbrowser"}
BAD_NAMES = {"exec", "eval", "compile", "__import__", "getattr", "setattr", "delattr", "globals", "vars", "breakpoint", "input"}
BAD_ATTRS = {"write_text", "write_bytes", "unlink", "mkdir", "rmdir", "rename", "touch", "chmod", "symlink_to", "hardlink_to",
             "system", "popen", "startfile", "remove", "removedirs", "makedirs"}


class 이미실행(Exception):
    pass


def log(msg):
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now()
        with open(LOGS / f"{now:%Y-%m-%d}.log", "a", encoding="utf-8") as f:
            f.write(f"{now:%H:%M:%S} {msg}\n")
    except OSError:
        pass


def write(path, text):
    """다 쓴 뒤 한 번에 바꿔 넣는다 (중간에 꺼져도 앞 파일이 남는다)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".쓰는중")
    tmp.write_text(text, encoding="utf-8", newline="\n")              # LF (CRLF 면 AI의 찾아 바꾸기가 실패한다)
    os.replace(tmp, path)


def version(folder):
    try:
        return (folder / "VERSION.txt").read_text(encoding="utf-8").strip() or "없음"
    except OSError:
        return "없음"


# ── 두 번 실행 막기 · 꺼졌던 자리 되살리기 ──

def alive(pid):
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    code = ctypes.c_ulong()
    k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return code.value == 259                              # STILL_ACTIVE


def lock():
    BASE.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                pid = int(LOCK.read_text(encoding="utf-8").strip() or 0)
            except (OSError, ValueError):
                pid = 0
            if pid and alive(pid):
                raise 이미실행()
            LOCK.unlink(missing_ok=True)                  # 꺼진 실행이 남긴 표시
    raise 이미실행()


def unlock():
    try:
        if LOCK.read_text(encoding="utf-8").strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def recover():
    """버전을 바꾸다 꺼진 경우를 되살린다"""
    if SWAP.exists():
        if not CUR.exists():
            SWAP.rename(CUR)
            log("되살림 : 교체중 → 현재")
        else:
            if PREV.exists():
                shutil.rmtree(SWAP, ignore_errors=True)
            else:
                SWAP.rename(PREV)
    shutil.rmtree(CAND, ignore_errors=True)
    if not CUR.exists() and PREV.exists():
        shutil.copytree(PREV, CUR)
        log("되살림 : 직전 → 현재")
    if not all((WPROG / f).exists() for f in FILES) or not (WPROG / "lib").exists():
        restore_work()


def restore_work():
    """AI작업실의 프로그램을 지금 쓰는 버전과 같게"""
    WPROG.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        shutil.copy2(CUR / f, WPROG / f)
    shutil.rmtree(WPROG / "lib", ignore_errors=True)
    shutil.copytree(CUR / "lib", WPROG / "lib", ignore=shutil.ignore_patterns("__pycache__"))


def digest(folder):
    h = hashlib.sha256()
    for f in FILES:
        p = folder / f
        h.update(f.encode() + (same_lines(p.read_bytes()) if p.exists() else b"(none)"))
    return h.hexdigest(), lib_digest(folder)


def lib_digest(folder):
    h = hashlib.sha256()
    lib = folder / "lib"
    for p in sorted(lib.rglob("*")) if lib.exists() else []:
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(lib)).encode() + same_lines(p.read_bytes()))
    return h.hexdigest()


def same_lines(b):
    """줄바꿈(CRLF · LF) 차이는 같은 것으로 본다"""
    return b.replace(b"\r\n", b"\n")


# ── 변환을 따로 돌리기 ──

def convert(program, files, timeout):
    """→ (파일마다 결과 목록 | None, 멈춘 까닭 | None)"""
    job = json.dumps({"program": str(program), "files": [str(f) for f in files]}, ensure_ascii=False).encode("utf-8")
    try:
        r = subprocess.run([sys.executable, "-I", "-B", str(TOOL / "변환실행.py")], input=job, capture_output=True,
                           timeout=timeout, creationflags=NO_WINDOW)
    except subprocess.TimeoutExpired:
        return None, f"{timeout}초 안에 끝나지 않음 (끝나지 않는 코드)"
    try:
        res = json.loads(r.stdout.decode("utf-8"))["results"]
    except (ValueError, KeyError):
        return None, "변환 프로그램이 도중에 멈춤"
    if res and "load" in res[0]:
        return None, f"변환 프로그램을 읽지 못함 — {res[0]['load']}"
    return res, None


# ── 실행 전 검사 · 시험 · 적용 ──

def inspect_code(path):
    """변환 프로그램에 파일 쓰기 · 다른 프로그램 · 인터넷 코드가 있는지"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        return [f"문법 오류 ({e.lineno}째 줄)"]
    found = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            found += [f"{a.name} 를 씀 ({n.lineno}째 줄)" for a in n.names if a.name.split(".")[0] in BAD_MODULES]
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in BAD_MODULES:
            found.append(f"{n.module} 를 씀 ({n.lineno}째 줄)")
        elif isinstance(n, ast.Name) and n.id in BAD_NAMES:
            found.append(f"{n.id} 를 씀 ({n.lineno}째 줄)")
        elif isinstance(n, ast.Attribute) and n.attr in BAD_ATTRS:
            found.append(f".{n.attr} 를 씀 ({n.lineno}째 줄)")
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open":
            mode = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == "mode"), None)
            if not (mode is None or (isinstance(mode, ast.Constant) and isinstance(mode.value, str) and not set(mode.value) & set("wax+"))):
                found.append(f"파일을 쓰는 open ({n.lineno}째 줄)")
    return sorted(set(found))


def test_cases():
    out = []
    for t in sorted(p for p in TESTS.iterdir() if p.is_dir()) if TESTS.exists() else []:
        src = next((p for p in sorted(t.iterdir()) if p.stem == "샘플입력"), None)
        exp = sorted(t.glob("기대*.html"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 1))
        if src and exp:
            out.append((t.name, src, [p.read_text(encoding="utf-8") for p in exp]))
    return out


def diff_lines(want, got, limit=8):
    import difflib
    out = []
    for w, g in zip(want + [""] * (len(got) - len(want)), got + [""] * (len(want) - len(got))):
        out += [l for l in difflib.unified_diff(w.splitlines(), g.splitlines(), lineterm="", n=0)
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return [re.sub(r'<p style="[^"]*">', "<p>", l) for l in out[:limit]]


def gate():
    """AI작업실의 프로그램이 바뀌었으면 검사 · 시험 → dict(결과, 버전, 까닭) 또는 None (바뀐 것 없음)"""
    if digest(WPROG) == digest(CUR):                            # 바뀐 것 없음 (앞서 남긴 시험 결과.md 는 AI가 읽도록 둔다)
        return None
    shutil.rmtree(CAND, ignore_errors=True)
    CAND.mkdir(parents=True)
    for f in FILES:
        if (WPROG / f).exists():
            shutil.copy2(WPROG / f, CAND / f)
    shutil.copytree(CUR / "lib", CAND / "lib")                  # lib 는 언제나 지금 쓰는 것 (AI 가 고치지 않는다)
    problems = []
    if lib_digest(WPROG) != lib_digest(CUR):
        problems.append("lib 폴더를 고쳤습니다 (lib 는 고치지 않습니다)")
    if not all((CAND / f).exists() for f in FILES):
        problems.append("변환.py 또는 변환설정.json 이 없습니다")
    else:
        try:
            json.loads((CAND / "변환설정.json").read_text(encoding="utf-8-sig"))
        except ValueError as e:
            problems.append(f"변환설정.json 이 깨졌습니다 ({e.lineno}째 줄)")
        problems += [f"쓰면 안 되는 코드 : {p}" for p in inspect_code(CAND / "변환.py")]
    detail, changed = [], []
    if not problems:
        cases = test_cases()
        res, stop = convert(CAND, [s for _, s, _ in cases], TEST_TIMEOUT)
        if stop:
            problems.append(f"시험 중 멈춤 : {stop}")
        else:
            for (name, _, want), r in zip(cases, res):
                if not r["ok"]:
                    problems.append(f"시험 기준 {name} : " + r.get("오류", r.get("안내", "")))
                    continue
                got = [d["html"] for d in r["docs"]]
                if got != want:                                 # 막지 않고 알린다
                    changed.append(name)
                    detail += [f"[{name}]  - 는 고치기 전, + 는 고친 뒤"] + ["  " + l for l in diff_lines(want, got)]
    if problems:
        shutil.rmtree(CAND, ignore_errors=True)
        write(WORK / "시험 결과.md", f"# 시험 결과 ({datetime.datetime.now():%Y-%m-%d %H:%M})\n\n"
              f"AI가 고친 변환 프로그램을 쓰지 않았습니다. 지금 버전 {version(CUR)}로 만들었습니다.\n"
              "고친 프로그램에 아래 문제가 있어 쓰지 않았습니다.\n\n## 까닭\n\n"
              + "\n".join(f"- {p}" for p in problems[:12]) + ("\n\n## 달라진 줄 (가린 샘플)\n\n```\n" + "\n".join(detail[:60]) + "\n```\n" if detail else "\n"))
        log(f"적용 안 함 : {problems[0][:120]}")
        return {"결과": "쓰지 않음", "까닭": problems, "버전": version(CUR)}
    old = version(CUR)
    new = next_version(old)
    (CAND / "VERSION.txt").write_text(new + "\n", encoding="utf-8")
    CUR.rename(SWAP)                                            # 현재 → 교체중 → 직전 (꺼지면 recover 가 되살린다)
    CAND.rename(CUR)
    shutil.rmtree(PREV, ignore_errors=True)
    SWAP.rename(PREV)
    n = len(test_cases())
    if changed:
        write(WORK / "시험 결과.md", f"# 시험 결과 ({datetime.datetime.now():%Y-%m-%d %H:%M})\n\n"
              f"AI가 고친 변환 프로그램을 버전 {new}로 적용했습니다. 다만 예전에 맞게 나오던 품의서 {n}건(시험 기준, 가린 샘플) 가운데 "
              f"{len(changed)}건의 모양이 바뀌었습니다. 고친 품의서에만 맞게 하려면 바뀐 품의서는 고치기 전 모양이 나오도록 다시 고칩니다.\n\n"
              "## 모양이 바뀐 품의서\n\n" + "\n".join(f"- {c}" for c in changed[:20])
              + "\n\n## 달라진 줄 (가린 샘플)\n\n```\n" + "\n".join(detail[:60]) + "\n```\n")
    else:
        (WORK / "시험 결과.md").unlink(missing_ok=True)
    after_version_change(f"적용 : 버전 {old} → {new} (" + (f"다른 품의서 {len(changed)}건 모양 바뀜" if changed else "다른 품의서 그대로") + ", 도구가 적음)")
    log(f"적용 {old} → {new}" + (f" · 모양 바뀜 {len(changed)}건" if changed else ""))
    return {"결과": "적용", "버전": new, "이전": old, "시험": n, "바뀜": changed}


def next_version(old):
    try:
        major, minor = old.split(".")
        return f"{major}.{int(minor) + 1}"
    except ValueError:
        return "1.0"


def after_version_change(line):
    write(WORK / "VERSION", version(CUR) + "\n")
    log_file = WORK / "CHANGELOG.md"
    try:
        text = log_file.read_text(encoding="utf-8")
    except OSError:
        text = "# CHANGELOG\n\n| 날짜 | 바꾼 것 |\n|---|---|\n"
    write(log_file, text.rstrip("\n") + f"\n| {datetime.date.today()} | {line} |\n")


# ── 만들기 ──

def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, TOOL / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_mask():
    return load_tool("마스킹")


def id_table():
    rows = {}
    try:
        for line in IDS.read_text(encoding="utf-8").splitlines():
            k, _, name = line.partition("\t")
            if re.fullmatch(r"건\d{4}", k) and name:
                rows[name] = k
    except (OSError, UnicodeDecodeError):
        pass
    return rows


def case_id(table, name):
    if name not in table:
        used = {int(k[1:]) for k in table.values()}
        table[name] = f"건{max(used, default=0) + 1:04d}"
    return table[name]


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|]', "_", s)[:80]


def inputs():
    IN.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in IN.iterdir() if p.is_file() and not p.name.startswith(("~$", ".")) and p.name.lower() not in SKIP)


def make(gate_result=None):
    global CMP
    CMP = load_tool("비교")
    table, made, skipped, read_errors = id_table(), [], [], []
    for path in inputs():
        res, stop = convert(CUR, [path], FILE_TIMEOUT)
        if stop or not res:
            skipped.append((path.name, f"변환하다 멈췄습니다 ({stop})"))
            read_errors.append(f"{path.suffix.lower() or '확장자 없는'} 파일 : {stop}")
            continue
        r = res[0]
        if not r["ok"]:
            if "안내" in r:
                skipped.append((path.name, r["안내"]))
            else:
                skipped.append((path.name, "변환 중 오류가 났습니다"))
                read_errors.append(f"{path.suffix.lower() or '확장자 없는'} 파일 : {r['오류']}")
            continue
        r["docs"] = [d for d in r["docs"] if any(any(c.strip() for row in b for c in row) if isinstance(b, list) else b.strip()
                                                     for b in d["blocks"])]      # 글자가 하나도 없는 건은 품의서로 보지 않는다
        if not r["docs"]:
            skipped.append((path.name, "품의서를 찾지 못했습니다 (pptx 는 「아래」 줄이 있는 슬라이드를 품의서로 봅니다)"))
            continue
        for i, d in enumerate(r["docs"], 1):
            k = case_id(table, f"{path.name} · 품의서{i}")
            name = f"{safe_name(path.stem)}_품의서{i} ({k})"
            try:
                write(OUT / f"{name}.html", d["html"])
            except OSError:
                skipped.append((f"{name}.html", "결과 파일이 다른 프로그램에서 열려 있어 바꾸지 못했습니다 — 그 프로그램을 닫고 다시 실행하세요"))
                continue
            made.append({"건": k, "이름": name, "원본": path.name, "rows": d["rows"], "blocks": d["blocks"], "html": d["html"],
                         "cmp": CMP.compare(d["blocks"], d["rows"])})
        log(f"만듦 {path.name} → {len(r['docs'])}건 (버전 {version(CUR)})" + (" · " + " · ".join(r["notes"]) if r["notes"] else ""))
    write(IDS, "".join(f"{k}\t{n}\n" for n, k in sorted(table.items(), key=lambda x: x[1])))
    write_samples(made)
    write_read_errors(read_errors)
    try:
        write(PAGE, page(made, skipped, gate_result))
    except OSError:
        print("  결과 페이지가 다른 프로그램에서 열려 있어 바꾸지 못했습니다. 그 프로그램을 닫고 다시 실행하세요.")
    return made, skipped


def write_samples(made):
    """양식만 남기고 가린 샘플 → AI작업실\\샘플\\건0000 (샘플입력.txt · 샘플_줄번호.txt)"""
    mask = load_mask()
    mk = mask.Masker()
    keep = set()
    for m in made:
        d = SAMPLES / m["건"]
        write(d / "샘플입력.txt", mask.to_text(mk.blocks(m["blocks"])))
        keep.add(m["건"])
    res, stop = convert(CUR, [SAMPLES / k / "샘플입력.txt" for k in sorted(keep)], TEST_TIMEOUT)
    for k, r in zip(sorted(keep), res or []):
        if r.get("ok") and r["docs"]:
            d = r["docs"][0]
            c = CMP.compare(d["blocks"], d["rows"])
            head = ([f"원본과 내용이 다른 줄 : {', '.join(map(str, sorted(c['rm'])))}"] if c["rm"] else []) + \
                   ([f"원본에 있는데 결과에서 빠진 곳 : {CMP.gap_text(c['gaps'])}"] if c["gaps"] else [])
            write(SAMPLES / k / "샘플_줄번호.txt", "\n".join(head + ([""] if head else []) + [numbered(d["rows"])]) + "\n")
    for old in SAMPLES.iterdir() if SAMPLES.exists() else []:   # 이번에 만들지 않은 건의 샘플은 치운다
        if old.is_dir() and old.name not in keep:
            shutil.rmtree(old, ignore_errors=True)


def write_read_errors(errors):
    f = WORK / "변환 오류.md"
    if not errors:
        f.unlink(missing_ok=True)
        return
    write(f, f"# 변환 오류 ({datetime.datetime.now():%Y-%m-%d %H:%M})\n\n지금 버전 {version(CUR)}의 변환 프로그램이 아래 파일을 바꾸다 멈췄습니다. "
          "파일 이름 · 내용은 적지 않습니다.\n\n" + "\n".join(f"- {e}" for e in errors) + "\n")


def visible(h):
    if h.lstrip().startswith("<table"):
        out = []
        for tr in re.findall(r"<tr>(.*?)</tr>", h, flags=re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S)]
            out.append("[표] " + " | ".join(cells))
        return out or ["[표]"]
    return [html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "", h))).replace(" ", " ")]


def numbered(rows):
    out = []
    for n, h in rows:
        for i, line in enumerate(visible(h)):
            out.append(f"{n:>4} | {line}" if n and i == 0 else f"     | {line}")
    return "\n".join(out)


# ── 결과 페이지 ──

PAGE_CSS = """
:root{--navy:#002452;--ink:#111;--body:#555;--muted:#767676;--line:#DDD;--bg:#F5F5F5;--red:#C50B2F;--redbg:#FAECEE;--ok:#1F6B3A;--okbg:#EAF2E8;--warnbg:#FFF6D6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans KR","맑은 고딕",sans-serif;letter-spacing:-0.02em}
::selection{background:var(--navy);color:#fff}
header{background:var(--navy);color:#fff;padding:18px 28px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
header h1{margin:0;font-size:20px}
header span{font-size:13px;color:#D5DCE6}
main{max-width:1000px;margin:0 auto;padding:20px 28px 60px}
.note{border-radius:10px;padding:12px 16px;margin:0 0 12px;font-size:14px;line-height:1.7}
.note b{display:block;font-size:15px}
.ok{background:var(--okbg);color:var(--ok)}
.bad{background:var(--redbg);color:var(--red)}
.warn{background:var(--warnbg);color:#6B4E00}
.note code{background:#fff;padding:1px 6px;border-radius:4px;color:var(--ink)}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 20px}
nav a{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 14px;font-size:13px;color:var(--navy);text-decoration:none}
section{margin:0 0 36px}
h2{font-size:17px;margin:0 0 4px}
.sub{font-size:13px;color:var(--muted);margin:0 0 10px}
.bar{display:flex;align-items:center;gap:12px;margin:0 0 10px}
button{background:var(--navy);color:#fff;border:0;border-radius:999px;padding:9px 20px;font:inherit;font-weight:700;font-size:14px;cursor:pointer}
button:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.msg{font-size:13px;color:var(--ok)}
.msg.bad{color:var(--red);background:none;padding:0}
.label{display:inline-block;background:var(--navy);color:#fff;font-size:12px;font-weight:700;padding:2px 10px;border-radius:4px;margin-right:8px}
.paper{background:#fff;border:2px solid var(--navy);padding:14px 0;overflow-x:auto}
.row.diff{background:#FFF1B8}
.diffnote{background:var(--warnbg);color:#6B4E00;border-radius:8px;padding:8px 12px;font-size:13px;margin:0 0 10px}
.row{display:grid;grid-template-columns:3.2em 45.5em;align-items:start}
.n{font-size:9pt;color:var(--muted);text-align:right;padding-right:.9em;user-select:none;line-height:18pt;font-family:"Noto Sans KR",sans-serif}
.c{font-family:"본고딕","Source Han Sans K","Noto Sans KR",sans-serif;font-size:12pt;min-width:0}
.c table{font-size:12pt}
textarea{width:100%;height:160px;margin-top:10px;font-family:Consolas,monospace;font-size:12px}
"""

PAGE_JS = """
function done(k,t,bad){var m=document.getElementById('msg-'+k);m.textContent=t;m.className='msg'+(bad?' bad':'');}
function copyCode(k){
  var t=document.getElementById('code-'+k);
  if(navigator.clipboard&&window.isSecureContext!==false){
    navigator.clipboard.writeText(t.value).then(function(){done(k,'복사했습니다. 전자결재 본문 편집기의 HTML 편집 화면에 붙여넣으세요.');},function(){fallback(k,t);});
  }else{fallback(k,t);}
}
function fallback(k,t){
  t.hidden=false;t.focus();t.select();
  var ok=false;try{ok=document.execCommand('copy');}catch(e){}
  if(ok){done(k,'복사했습니다. 전자결재 본문 편집기의 HTML 편집 화면에 붙여넣으세요.');}
  else{done(k,'자동 복사가 막혔습니다. 아래 칸이 선택되어 있으니 Ctrl+C 를 누르세요.',true);}
}
"""


def page(made, skipped, g):
    e = html.escape
    notes = []
    if g and g["결과"] == "적용" and g["바뀜"]:
        notes.append(f'<div class="note warn"><b>AI가 고친 버전을 적용했습니다 (버전 {e(g["버전"])}). 다른 품의서 {len(g["바뀜"])}건의 모양도 바뀌었습니다</b>'
                     f'예전에 맞게 나오던 품의서 {g["시험"]}건 가운데 {len(g["바뀜"])}건이 고치기 전과 다르게 나옵니다. '
                     f'고친 품의서에만 맞게 하려면 ChatGPT 앱의 「01_품의서 AI작업실」에 <code>{FIX_NARROW}</code> 라고 보내세요. '
                     f'바로 되돌리려면 <code>이전 버전으로.bat</code>을 실행하세요 (버전 {e(g["이전"])}로 돌아갑니다).</div>')
    elif g and g["결과"] == "적용":
        notes.append(f'<div class="note ok"><b>AI가 고친 버전을 적용했습니다 (버전 {e(g["버전"])})</b>'
                     f'예전에 맞게 나오던 품의서 {g["시험"]}건도 그대로 나옵니다. 원본과 비교한 뒤 복사하세요. '
                     f'마음에 들지 않으면 <code>이전 버전으로.bat</code>을 실행하세요 (버전 {e(g["이전"])}로 돌아갑니다).</div>')
    elif g:
        notes.append(f'<div class="note bad"><b>AI가 고친 프로그램을 쓰지 않았습니다</b>'
                     f'{e(g["까닭"][0])}{" 외 " + str(len(g["까닭"]) - 1) + "건" if len(g["까닭"]) > 1 else ""}. '
                     f'지금 결과는 버전 {e(g["버전"])}로 만들었습니다. ChatGPT 앱의 「01_품의서 AI작업실」에 '
                     f'<code>{FIX_TEST}</code> 라고 보내세요.</div>')
    if skipped:
        items = "".join(f"<br>· {e(n)} — {e(r)}" for n, r in skipped)
        tail = f' 변환 중 오류가 난 파일은 ChatGPT 앱에 <code>{FIX_READ}</code> 라고 보내세요.' if any("오류" in r or "멈췄" in r for _, r in skipped) else ""
        notes.append(f'<div class="note warn"><b>만들지 못한 파일 {len(skipped)}개</b>{items}<br>{tail}</div>')
    diffs = [m for m in made if m["cmp"]["rm"] or m["cmp"]["lm"]]
    if diffs:
        notes.append('<div class="note warn"><b>원본과 내용이 다른 품의서 ' + str(len(diffs)) + '건</b>'
                     + " · ".join(f'<a href="#{m["건"]}">{e(m["이름"])}</a>' for m in diffs)
                     + '<br>노란 줄을 원본과 비교하고, 고칠 곳은 건 번호와 줄번호로 ChatGPT 앱에 말하세요.</div>')
    if not made and not skipped:
        notes.append('<div class="note warn"><b>01_품의서 넣기 폴더가 비어 있습니다</b>품의서 파일을 넣고 <code>품의서 만들기.bat</code>을 다시 실행하세요.</div>')
    nav = "".join(f'<a href="#{m["건"]}">{e(m["이름"])}</a>' for m in made)
    secs = []
    for m in made:
        rows, cur, cmp = [], 0, m["cmp"]
        for n, h in m["rows"]:
            cur = n or cur
            cls = "row diff" if cur in cmp["rm"] else "row"
            rows.append(f'<div class="{cls}"><span class="n">{n or ""}</span><div class="c">{h}</div></div>')
        n_diff = len(cmp["rm"]) + len(cmp["lm"])
        note = ""
        if n_diff:
            note = (f'<div class="diffnote">원본과 내용이 다른 곳이 있습니다. 노란 줄을 원본 파일과 비교하세요'
                    + (f' · 원본 내용이 <b>{CMP.gap_text(cmp["gaps"])}</b>에서 빠졌습니다' if cmp["gaps"] else "") + ".</div>")
        body = "\n".join(h for _, h in m["rows"])
        secs.append(f'<section id="{m["건"]}"><h2><span class="label">HTML 품의서</span>{e(m["이름"])}</h2>'
                    f'<p class="sub">원본 : {e(m["원본"])} · 전자결재와 같은 폭 · 본고딕 12pt · 줄간격 1.5 · 왼쪽 숫자는 줄번호 (복사되지 않습니다)</p>'
                    f'<div class="bar"><button type="button" onclick="copyCode(\'{m["건"]}\')">HTML 코드 복사</button>'
                    f'<span class="msg" id="msg-{m["건"]}" role="status"></span></div>'
                    f'{note}<div class="paper">{"".join(rows)}</div>'
                    f'<textarea id="code-{m["건"]}" hidden readonly>{e(body)}</textarea></section>')
    return (f'<!DOCTYPE html>\n<html lang="ko"><head><meta charset="utf-8"><title>HTML 품의서 확인</title><style>{PAGE_CSS}</style></head><body>'
            f'<header><h1>HTML 품의서 확인</h1><span>변환 프로그램 버전 {e(version(CUR))} · {datetime.datetime.now():%Y-%m-%d %H:%M} 만듦</span></header>'
            f'<main>{"".join(notes)}<p class="sub">품의서 서식을 확인하세요. 서식이 맞으면 「HTML 코드 복사」, 다르면 ChatGPT 앱의 「01_품의서 AI작업실」에 '
            f'건 번호와 줄번호로 말하세요. 예) <code>건0003 9번 줄 바로 아래에 표가 들어가야 해. 이것만 고쳐 줘.</code></p>'
            f'<nav>{nav}</nav>{"".join(secs)}</main><script>{PAGE_JS}</script></body></html>\n')


def open_page():
    if os.environ.get("품의서_열지않기"):
        return
    try:
        os.startfile(PAGE)
    except (AttributeError, OSError):
        pass


# ── 되돌리기 ──

def rollback():
    if not PREV.exists():
        print("되돌릴 이전 버전이 없습니다.")
        return False
    old, new = version(CUR), version(PREV)
    CUR.rename(SWAP)
    PREV.rename(CUR)
    SWAP.rename(PREV)
    restore_work()
    (WORK / "시험 결과.md").unlink(missing_ok=True)
    after_version_change(f"되돌리기 : 버전 {old} → {new} (도구가 적음)")
    log(f"되돌리기 {old} → {new}")
    print(f"버전 {old} → {new} 로 되돌렸습니다.")
    return True


def main():
    cmd = {"make": "만들기", "rollback": "되돌리기"}.get(sys.argv[1], sys.argv[1]) if len(sys.argv) > 1 else "만들기"
    try:
        lock()
    except 이미실행:
        print("\n  품의서 만들기가 이미 실행 중입니다. 앞의 검은 창이 끝날 때까지 기다리세요.\n")
        sys.exit(2)
    try:
        recover()
        g = None
        if cmd == "되돌리기":
            rollback()
        else:
            print("  AI가 고친 것이 있는지 보고 있습니다 …")
            g = gate()
            if g:
                print(f"  {'새 버전 ' + g['버전'] + ' 적용' if g['결과'] == '적용' else 'AI가 고친 것을 쓰지 않음'}")
        print("  품의서를 HTML 로 만드는 중입니다 …")
        made, skipped = make(g)
        print(f"  만듦 {len(made)}건" + (f" · 만들지 못한 파일 {len(skipped)}개" if skipped else ""))
        open_page()
    except Exception as e:
        log("멈춤 " + "".join(traceback.format_exception(type(e), e, e.__traceback__))[-1500:])
        print("\n  품의서 만들기가 멈췄습니다.")
        print("  「이전 버전으로.bat」을 실행해 보세요. 그래도 멈추면 보조강사에게 이 화면을 보여 주세요.")
        print(f"  ({type(e).__name__})\n")
        sys.exit(1)
    finally:
        unlock()


if __name__ == "__main__":
    main()
