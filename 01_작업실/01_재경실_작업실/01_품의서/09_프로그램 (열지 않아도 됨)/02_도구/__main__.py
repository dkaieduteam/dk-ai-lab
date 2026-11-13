# -*- coding: utf-8 -*-
"""01_품의서 의 bat 이 이 폴더(02_도구)를 그대로 python 에 넘기면 이 파일이 실행.py 를 부른다.
bat 파일에는 한글을 쓰지 않는다 (명령 창이 한글 줄을 잘못 끊어 읽는 PC가 있다). 인자 : make · rollback"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "실행.py"), run_name="__main__")
