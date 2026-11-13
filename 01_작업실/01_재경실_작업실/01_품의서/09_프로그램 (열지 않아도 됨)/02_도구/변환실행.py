# -*- coding: utf-8 -*-
"""변환 프로그램을 따로 떨어진 프로세스에서 돌린다. 실행.py 가 부른다 (시간 제한 · 끝나지 않는 코드 대비).

    python -I -B 변환실행.py      표준 입력 = {"program": 변환 프로그램 폴더, "files": [파일, …]}
                                  표준 출력 = 파일마다 {"ok": true, "docs": [{"blocks", "rows", "html"}]}
                                              또는 {"ok": false, "안내": 읽지 못한 까닭} · {"ok": false, "오류": 오류 종류와 줄}
이 파일은 결과를 화면(표준 출력)으로만 돌려준다. 파일을 만들지 않는다.
"""
import contextlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path


def where(e):
    """오류 종류 · 변환.py 의 줄 (값 · 경로는 쓰지 않는다)"""
    lines = [f"{Path(f.filename).name} {f.lineno}째 줄 · {f.name}" for f in traceback.extract_tb(e.__traceback__)
             if Path(f.filename).name == "변환.py"]
    return f"{type(e).__name__}" + (f" ({lines[-1]})" if lines else "")


def main():
    job = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    folder = Path(job["program"])
    sys.path.insert(0, str(folder / "lib"))
    out = []
    with contextlib.redirect_stdout(sys.stderr):                    # 변환 프로그램이 화면에 쓰는 글은 결과와 섞이지 않게
        run(folder, job["files"], out)
    sys.stdout.buffer.write(json.dumps({"results": out}, ensure_ascii=False).encode("utf-8"))


def run(folder, files, out):
    try:
        spec = importlib.util.spec_from_file_location("변환", folder / "변환.py")
        conv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conv)
    except Exception as e:
        out.append({"load": where(e)})
        return
    for f in files:
        try:
            conv.NOTES.clear()
            docs = conv.read(Path(f))
            out.append({"ok": True, "notes": list(conv.NOTES),
                        "docs": [{"blocks": b, "rows": conv.rows(b), "html": conv.to_html(b)} for b in docs]})
        except conv.읽기안내 as e:
            out.append({"ok": False, "안내": str(e)})
        except PermissionError:
            out.append({"ok": False, "안내": "다른 프로그램에서 열려 있어 읽지 못했습니다 — 그 프로그램을 닫고 다시 실행하세요"})
        except FileNotFoundError:
            out.append({"ok": False, "안내": "파일이 없어졌습니다 — 다시 넣고 실행하세요"})
        except Exception as e:
            out.append({"ok": False, "오류": where(e)})


if __name__ == "__main__":
    main()
