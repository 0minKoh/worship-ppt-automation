# utils/crawl.py

import requests
from bs4 import BeautifulSoup
import re # 정규표현식 모듈 임포트

def crawl_lyrics(url: str) -> str:
    """
    주어진 URL에서 찬양 가사를 크롤링합니다.
    현재는 Bugs (벅스) 사이트에서 가사를 크롤링하도록 구현되어 있습니다.
    """
    # URL이 벅스 사이트인지 확인
    if not url.startswith("https://music.bugs.co.kr/"):
        raise ValueError("현재는 벅스 사이트에서만 가사를 크롤링할 수 있습니다. URL을 확인해주세요.")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생

        soup = BeautifulSoup(response.text, 'html.parser')

        lyrics: str = soup.select_one('div.lyricsContainer xmp').get_text()
        return lyrics

    except requests.exceptions.RequestException as e:
        print(f"Error during web request for {url}: {e}")
        return f"가사 크롤링 중 네트워크 오류 발생: {e}"
    except Exception as e:
        print(f"Error during lyrics crawling for {url}: {e}")
        return f"가사 크롤링 중 예상치 못한 오류 발생: {e}"

