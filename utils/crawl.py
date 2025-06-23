# utils/crawl.py

import requests
from bs4 import BeautifulSoup
import re # 정규표현식 모듈 임포트

def crawl_lyrics(url: str) -> str:
    """
    주어진 URL에서 찬양 가사를 크롤링합니다.
    이 함수는 실제 웹사이트 구조에 따라 변경될 수 있습니다.
    여기서는 멜론/벅스 뮤직 같은 일반적인 가사 페이지를 가정합니다.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생

        soup = BeautifulSoup(response.text, 'html.parser')

        # 가사를 찾기 위한 일반적인 CSS 선택자 또는 태그 조합 (예시)
        # 실제 웹사이트마다 가사 엘리먼트의 id, class, 태그 구조가 다릅니다.
        # 따라서 이 부분은 실제 크롤링 대상 웹사이트의 HTML 구조를 분석하여 수정해야 합니다.
        lyrics: str = soup.select_one('div.lyricsContainer xmp').get_text()
        return lyrics

    except requests.exceptions.RequestException as e:
        print(f"Error during web request for {url}: {e}")
        return f"가사 크롤링 중 네트워크 오류 발생: {e}"
    except Exception as e:
        print(f"Error during lyrics crawling for {url}: {e}")
        return f"가사 크롤링 중 예상치 못한 오류 발생: {e}"

