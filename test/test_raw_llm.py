# --- 테스트 시나리오를 위한 샘플 데이터 ---
import os
import sys



# 프로젝트 루트 디렉토리를 sys.path에 추가하여 모듈 임포트 가능하게 함
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# crawl.py에서 SAMPLE_SONG_TITLE과 SAMPLE_FULL_LYRICS를 크롤링합니다.
from utils.crawl import crawl_lyrics

from utils.llm import SplittedLyricsResponse, split_lyrics_to_json


def test():
    # 샘플 곡 제목과 가사
    SAMPLE_SONG_TITLE = "은혜 아니면"
    SAMPLE_FULL_LYRICS = crawl_lyrics("https://music.bugs.co.kr/track/2844343")

    input_data = [
        {"title": SAMPLE_SONG_TITLE, "lyrics": SAMPLE_FULL_LYRICS}
    ]

    # Crawl된 가사를 테스트합니다.
    # print(f"Sample Song Title: {SAMPLE_SONG_TITLE}")
    # print(f"Sample Full Lyrics:\n{SAMPLE_FULL_LYRICS[:100]}...")  # 가사 일부만 출력하여 길이 제한

    result: list = split_lyrics_to_json(input_data)

    # LLM을 사용하여 가사를 분할한 결과를 출력합니다.
    print("Split Lyrics Result:")
    for item in result:
        print(f"Processed Lyrics Chunk: {item}")

test()