# tests/test_crawl.py

import os
import sys
from unittest.mock import patch, Mock
import requests # requests 임포트 (requests.exceptions.RequestException을 위해)

# 프로젝트 루트 디렉토리를 sys.path에 추가하여 모듈 임포트 가능하게 함
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 테스트 대상 함수 임포트
from utils.crawl import crawl_lyrics


# --- 테스트 함수 정의 ---
def run_tests():
    print("\n--- Testing crawl_lyrics function ---")

    # 테스트 1: 성공적인 가사 크롤링 (유효한 Bugs URL)
    print("\n--- Test 1: Successful lyrics crawling (Valid Bugs URL) ---")
    bugs_url_success = "https://music.bugs.co.kr/track/7004582?wl_ref=list_tr_08_mab"
    lyrics: str = crawl_lyrics(bugs_url_success)
    print("Output:", lyrics)

    print("\n--- All crawl_lyrics tests attempted. Check logs for 'Passed!' messages. ---")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\nAn unexpected error occurred during tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # sys.path에서 추가된 경로 제거 (깔끔하게)
        project_root = os.path.dirname(os.path.dirname(__file__))
        if project_root in sys.path:
            sys.path.remove(project_root)