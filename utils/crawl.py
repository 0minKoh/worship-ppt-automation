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

        lyrics_element = soup.select_one('div.lyricsContainer xmp')
        if not lyrics_element:
            # 해당 선택자로 가사를 찾지 못하면 다른 일반적인 선택자도 시도할 수 있습니다.
            # 예: lyrics_element = soup.find('div', class_='lyrics')
            # 현재는 div.lyricsContainer xmp 만 지원하므로, 없으면 오류로 간주
            raise ValueError("Bugs 사이트에서 가사 컨테이너(div.lyricsContainer xmp)를 찾을 수 없습니다.")
        
        else:
            lyrics_text: str = lyrics_element.get_text()
            
            # --- 크롤링된 가사 정제 로직 추가 ---
            # 1. _x000D_ 문자열 제거 (XML에서 \r을 나타냄)
            lyrics_text = lyrics_text.replace('_x000D_', '').strip()
            
            # 2. 여러 개의 줄바꿈을 하나로 줄임 (과도한 빈 줄 방지)
            lyrics_text = re.sub(r'\n\s*\n+', '\n\n', lyrics_text)
            
            # 3. 각 줄의 앞뒤 공백 제거
            lyrics_lines = [line.strip() for line in lyrics_text.split('\n')]
            lyrics_text = '\n'.join(lyrics_lines)
            
            # 4. 전체 텍스트의 불필요한 공백 제거
            lyrics_text = lyrics_text.strip()

            return lyrics_text

    except requests.exceptions.RequestException as e:
        print(f"Error during web request for {url}: {e}")
        return f"가사 크롤링 중 네트워크 오류 발생: {e}"
    except ValueError as e: # 새롭게 추가된 ValueError (가사 컨테이너 못 찾음)
        print(f"Error during lyrics crawling for {url}: {e}")
        return f"가사 크롤링 중 오류 발생: {e}"
    except Exception as e:
        print(f"Error during lyrics crawling for {url}: {e}")
        return f"가사 크롤링 중 예상치 못한 오류 발생: {e}"

