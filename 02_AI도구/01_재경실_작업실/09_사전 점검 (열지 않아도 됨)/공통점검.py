# -*- coding: utf-8 -*-
"""사전 점검 공통 기능 — 과정마다 고치지 않고 그대로 복사한다 (교안-세트 skill assets/사전점검_GUI).

- 빠진 파일 : zip 을 만들 때(build_배포zip.py) 세트에 실제로 든 파일을 "파일목록.txt"에 적어 두고, 점검은 그 목록만 본다.
  공개본 · 전체본 어느 쪽이든 점검 스크립트를 손으로 고칠 일이 없다.
- 예전 skill : 교육 때 새로 설치할 skill 이 이미 깔려 있으면 지우지 않고 skill 폴더 밖 백업 폴더로 옮긴다.
"""
import datetime
import os
import shutil
from pathlib import Path

LIST_NAME = "파일목록.txt"


def missing_files(root: Path, here: Path):
    """(빠진 파일 목록, 목록 파일이 있는가). 목록은 세트 폴더 기준 상대경로 한 줄에 하나"""
    lst = here / LIST_NAME
    if not lst.exists():
        return [], False
    want = [l.strip() for l in lst.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    return [w for w in want if not (root / w).exists()], True


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def move_old_skills(names):
    """새로 설치할 skill 이 이미 있으면 skills_백업/<이름>_<시각> 으로 옮긴다.
    돌려주는 값 = [(이름, 옮긴 곳 또는 None(옮기지 못함))] — 없던 skill 은 빠진다"""
    skills = codex_home() / "skills"
    backup = codex_home() / "skills_백업"
    stamp = f"{datetime.datetime.now():%Y%m%d_%H%M}"
    done = []
    for name in names:
        src = skills / name
        if not src.exists():
            continue
        dst = backup / f"{name}_{stamp}"
        try:
            backup.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            done.append((name, dst if not src.exists() else None))
        except Exception:
            done.append((name, None))
    return done
