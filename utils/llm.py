import requests
import json
import os
from django.conf import settings # Django settings에서 API 키를 가져오기 위함

# Gemini API 설정
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_MODEL = "gemini-2.0-flash"

def _call_gemini_api(prompt_parts: list, response_schema: dict = None) -> dict:
    """
    Gemini API에 직접 요청을 보내고 JSON 응답을 파싱합니다.
    """
    api_key = settings.GEMINI_API_KEY # settings.py에서 API 키를 가져옵니다.
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 Django settings에 설정되지 않았습니다.")

    headers = {
        'Content-Type': 'application/json'
    }

    # API 요청 페이로드 구성
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": prompt_parts # 프롬프트는 텍스트 파트 리스트로 전달됩니다.
            }
        ]
    }

    # 스키마가 정의된 경우 generationConfig 추가 (structured output)
    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    
    # API 호출 URL에 API 키 추가
    api_endpoint = f"{GEMINI_API_URL}?key={api_key}"

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생 (4xx, 5xx)
        
        result = response.json()
        
        if result.get("candidates") and result["candidates"][0].get("content") \
           and result["candidates"][0]["content"].get("parts") \
           and result["candidates"][0]["content"]["parts"][0].get("text"):
            
            # structured output의 경우 text 필드에 JSON 문자열이 담겨 있습니다.
            # 이를 다시 JSON 객체로 파싱합니다.
            if response_schema:
                try:
                    return json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Gemini API 응답이 유효한 JSON이 아닙니다: {e}. 응답: {result['candidates'][0]['content']['parts'][0]['text']}")
            else:
                # 일반 텍스트 응답의 경우
                return {"text": result["candidates"][0]["content"]["parts"][0]["text"]}
        else:
            raise ValueError(f"Gemini API 응답 형식이 예상과 다릅니다: {result}")

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Gemini API 요청 중 네트워크 오류 발생: {e}")
    except ValueError as e:
        raise e # 위에 정의된 사용자 정의 ValueError
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 중 예상치 못한 오류 발생: {e}")


def make_requirements_of_paster_json(user_input_text: str) -> dict:
    """
    사용자 입력 텍스트를 파싱하여 예배 정보에 필요한 JSON 데이터를 생성합니다.
    Gemini LLM을 사용하여 텍스트를 구조화합니다.
    """
    response_schema = {
        "type": "object",
        "properties": {
            "NAME_OF_PRAYER": {"type": "string", "description": "기도자 이름 (예: 홍길동)"},
            "NAME_OF_OFFERING": {"type": "string", "description": "봉헌자 이름 (예: 김철수)"},
            "NAME_OF_ADS_MANAGER": {"type": "string", "description": "광고 담당자 이름 (예: 이영희)"}, # 필드명 변경: NAME_OF_ADS -> NAME_OF_ADS_MANAGER
            "BIBLE_RANGE": {
                "type": "object",
                "properties": {
                    "BIBLE_BOOK": {"type": "string", "description": "성경 책 이름 (예: 요한복음)"},
                    "BIBLE_CH_BEGIN": {"type": "integer", "description": "시작 장 (예: 1)"},
                    "BIBLE_VERSE_BEGIN": {"type": "integer", "description": "시작 절 (예: 1)"},
                    "BIBLE_CH_END": {"type": "integer", "description": "끝 장 (예: 3)"},
                    "BIBLE_VERSE_END": {"type": "integer", "description": "끝 절 (예: 16)"}
                },
                "required": ["BIBLE_BOOK", "BIBLE_CH_BEGIN", "BIBLE_VERSE_BEGIN", "BIBLE_CH_END", "BIBLE_VERSE_END"]
            },
            "TITLE_OF_SERMON": {"type": "string", "description": "설교 제목"},
            "ENDING_SONG_TITLE": {"type": "string", "description": "결단 찬양 제목"},
            "BENEDICTION_MINISTER": {"type": "string", "description": "축도자 이름"}, # 필드명 변경: ENDING_PRAYER -> BENEDICTION_MINISTER
            "ads_content_list": { # 필드명 변경: ads -> ads_content_list
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "광고 제목"},
                        "contents": {"type": "string", "description": "광고 내용"}
                    },
                    "required": ["title", "contents"]
                },
                "description": "광고 목록 (제목과 내용 포함)"
            }
        },
        "required": ["NAME_OF_PRAYER", "NAME_OF_OFFERING", "NAME_OF_ADS_MANAGER", "BIBLE_RANGE", "TITLE_OF_SERMON", "ENDING_SONG_TITLE", "BENEDICTION_MINISTER", "ads_content_list"]
    }

    prompt_parts = [
        {"text": f"""
        다음 사용자 입력 텍스트에서 예배 PPT 생성에 필요한 정보를 추출하여 JSON 형식으로 구조화해 주세요.
        응답은 반드시 JSON 스키마에 따라야 합니다. 광고 내용은 배열 내의 객체 형태로 제공되어야 합니다.

        사용자 입력 텍스트:
        {user_input_text}
        """}
    ]
    
    try:
        return _call_gemini_api(prompt_parts, response_schema)
    except Exception as e:
        print(f"Error in make_requirements_of_paster_json: {e}")
        return {}


def split_lyrics_to_json(crawled_text_list: list) -> list:
    """
    크롤링된 가사 리스트를 Gemini LLM을 사용하여 PPT 페이지 단위로 분할합니다.
    """
    results = []
    for item in crawled_text_list:
        title = item.get("title", "알 수 없는 곡")
        lyrics = item.get("lyrics", "")

        if not lyrics:
            print(f"Warning: No lyrics found for '{title}'. Skipping split.")
            results.append({"title": title, "splitted_lyrics": []})
            continue

        response_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "찬양 제목"},
                "splitted_lyrics": {
                    "type": "array",
                    "items": {"type": "string", "description": "한 페이지에 들어갈 가사 블록"},
                    "description": "가사가 PPT 페이지별로 분할된 리스트"
                }
            },
            "required": ["title", "splitted_lyrics"]
        }

        prompt_parts = [
            {"text": f"""
            다음 찬양 가사를 PPT 슬라이드에 적합한 길이로 나누어 주세요.
            각 슬라이드에는 너무 많은 텍스트가 들어가지 않도록 적절히 분할해야 합니다.
            후렴구는 반복될 수 있습니다. 응답은 반드시 JSON 스키마에 따라야 합니다.

            찬양 제목: {title}
            전체 가사:
            {lyrics}
            """}
        ]

        try:
            # _call_gemini_api는 JSON 객체를 반환하므로 바로 사용할 수 있습니다.
            result = _call_gemini_api(prompt_parts, response_schema)
            results.append(result)
        except Exception as e:
            print(f"Error splitting lyrics for '{title}' with Gemini API: {e}")
            results.append({"title": title, "splitted_lyrics": [lyrics]}) # 오류 시 전체 가사를 한 페이지로
    
    return results


def get_bible_contents(bible_book: str, begin_ch: int, begin_verse: int, end_ch: int, end_verse: int) -> list:
    """
    성경 구절 범위를 입력받아 Gemini LLM을 통해 성경 내용을 가져오는 함수.
    실제 구현에서는 성경 API 또는 DB에서 가져와야 하지만, 여기서는 LLM을 통해 임시로 생성합니다.
    """
    response_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "성경 구절 제목 (예: 요한복음 1:1)"},
                "contents": {"type": "string", "description": "성경 구절 내용"}
            },
            "required": ["title", "contents"]
        }
    }

    prompt_parts = [
        {"text": f"""
        다음 성경 구절의 내용을 한국어로 제공해 주세요. 각 절을 별도의 객체로 분리하여 배열에 담고, 'title'에는 '책이름 장:절', 'contents'에는 해당 절의 내용을 넣어주세요.

        성경 구절: {bible_book} {begin_ch}:{begin_verse} - {end_ch}:{end_verse}
        """}
    ]

    try:
        # _call_gemini_api는 JSON 객체를 반환하므로 바로 사용할 수 있습니다.
        return _call_gemini_api(prompt_parts, response_schema)
    except Exception as e:
        print(f"Error getting Bible contents with Gemini API: {e}")
        return [{"title": f"{bible_book} {begin_ch}:{begin_verse}-{end_ch}:{end_verse}", "contents": "성경 내용을 가져오지 못했습니다."}]

