# utils/llm.py

import google.genai as genai
import json
import os
import re
from django.conf import settings
from pydantic import BaseModel, Field # <--- Pydantic BaseModel, Field 임포트
from typing import List # <--- List 타입 힌트 임포트


# --- Pydantic 모델 정의: LLM의 structured output을 위한 스키마 ---
# 찬양 가사 분할을 위한 응답 스키마
class SplittedLyricsResponse(BaseModel):
    title: str = Field(description="찬양 제목")
    splitted_lyrics: List[str] = Field(description="가사가 PPT 페이지별로 분할된 리스트")


def _call_gemini_api(prompt_parts: str, response_schema: BaseModel = None) -> dict: # response_schema를 BaseModel 타입으로 힌트
    """
    Gemini API에 요청을 보내고 JSON 응답을 파싱합니다.
    google.genai 라이브러리를 활용합니다. Pydantic 모델을 response_schema로 받을 수 있습니다.
    """
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        raise ValueError("GEMINI_API_KEY가 Django settings에 설정되지 않았습니다.")


    client: genai.Client = genai.Client(api_key=api_key)

    generation_config_params = {}
    if response_schema:
        # Pydantic 모델을 직접 response_schema로 전달
        generation_config_params["response_mime_type"] = "application/json"
        generation_config_params["response_schema"] = response_schema
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_parts,
            config=generation_config_params
        )

        print("응답 완료")

        if response.text is None:
            raise ValueError("Gemini API 응답에 텍스트가 없습니다.")
        # 응답 텍스트를 JSON으로 파싱
        response_text = response.text.strip()
        if not response_text:
            raise ValueError("Gemini API 응답이 비어 있습니다.")
        try:
            response_json = json.loads(response_text)
            return response_json
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini API 응답을 JSON으로 파싱하는 중 오류 발생: {e}")

        
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 중 예상치 못한 오류 발생: {e}")


# def _remove_consecutive_duplicates(chunks: list) -> list:
#     """
#     연속으로 반복되는 가사 덩어리(슬라이드)를 제거합니다.
#     """
#     if not chunks:
#         return []
#     cleaned_chunks = [chunks[0]]
#     for i in range(1, len(chunks)):
#         if chunks[i].strip() != cleaned_chunks[-1].strip():
#             cleaned_chunks.append(chunks[i])
#     return cleaned_chunks

# def _rewrap_lyrics_chunk(chunk_text: str, max_line_len: int = 15, max_lines_per_chunk: int = 4) -> str:
#     """
#     가사 덩어리의 줄을 재조정하여 각 줄이 최대 글자 수를 넘지 않고,
#     전체 덩어리가 최대 줄 수를 넘지 않도록 합니다.
#     """
#     lines = []
#     current_line_words = []
#     current_line_len = 0

#     initial_lines = chunk_text.split('\n')

#     for line_from_llm in initial_lines:
#         words = line_from_llm.split(' ')
#         for word in words:
#             if current_line_words and (current_line_len + len(word) + 1 > max_line_len):
#                 lines.append(' '.join(current_line_words))
#                 current_line_words = [word]
#                 current_line_len = len(word)
#             else:
#                 current_line_words.append(word)
#                 current_line_len += len(word) + (1 if current_line_words else 0)

#         if current_line_words:
#             lines.append(' '.join(current_line_words))
#             current_line_words = []
#             current_line_len = 0
    
#     final_chunk_lines = lines[:max_lines_per_chunk]

#     return '\n'.join(final_chunk_lines)


def split_lyrics_to_json(crawled_text_list: list) -> list:
    """
    크롤링된 가사 리스트를 Gemini LLM을 사용하여 PPT 페이지 단위로 분할하고 후처리합니다.
    - LLM에게 3-4줄, 15자 제한, 중복 피하기를 요청
    - 파이썬 후처리로 연속 중복 제거 및 줄바꿈 재조정
    """
    results = []
    for item in crawled_text_list:
        title = item.get("title", "알 수 없는 곡")
        lyrics = item.get("lyrics", "")

        if not lyrics:
            print(f"Warning: No lyrics found for '{title}'. Skipping split.")
            results.append({"title": title, "splitted_lyrics": ["가사를 가져올 수 없습니다."]})
            continue
        

        lines = lyrics.split('\n')
        chunk_size = 5
        fallback_lyrics_pages = ["\n".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size) if "\n".join(lines[i:i + chunk_size]).strip()]
        if not fallback_lyrics_pages:
            fallback_lyrics_pages = ["가사 분할 중 오류 발생."]
        results.append({"title": title, "splitted_lyrics": fallback_lyrics_pages})

        # 시간 관계상, LLM 호출이 아닌 fallback 데이터를 사용합니다. (자동 분할)
        # prompt_parts = f"""
        #     다음 찬양 가사를 PPT 슬라이드에 적합하게 분할해 주세요.
        #     각 슬라이드(가사 블록)는 의미적으로 3-4줄을 유지하도록 노력해주세요.
        #     각 줄은 공백을 포함하여 최대 15자를 넘지 않도록 해주세요.
        #     반복되는 후렴구는 가능한 한 중복을 피해서 간결하게 처리하거나,
        #     반복되는 슬라이드를 최소화하여 가사 전체를 효율적으로 표현해주세요.

        #     리스트 형태: ["슬라이드1에 들어갈 찬양가사 1번째 줄\n슬라이드1에 들어갈 찬양가사 2번째 줄\n...", "슬라이드2에 들어갈 찬양가사 1번째 줄\n슬라이드2에 들어갈 찬양가사 2번째 줄\n...", ...]

        #     찬양 제목: {title}
        #     전체 가사:
        #     {lyrics}
        #     """
        # print("--- LLM 요청 시작 ---")
        # try:
        #     # Pydantic 모델을 response_schema로 전달
        #     # _call_gemini_api는 이제 BaseModel 인스턴스를 반환하므로, 이를 dict로 변환
        #     response_parsed_data = _call_gemini_api(prompt_parts, SplittedLyricsResponse) # <--- SplittedLyricsResponse 전달
            
        #     # --- LLM 응답 후처리 ---
        #     # llm_splitted_lyrics = response_parsed_data.get('splitted_lyrics', [])
            
        #     # 1. 연속 중복 슬라이드 제거
        #     # cleaned_lyrics = _remove_consecutive_duplicates(llm_splitted_lyrics)
        #     # 2. 각 슬라이드의 줄바꿈 및 글자 수 재조정
        #     # for chunk_text in cleaned_lyrics:
        #     #     final_rewrapped_lyrics.append(_rewrap_lyrics_chunk(chunk_text, max_line_len=15, max_lines_per_chunk=4))
            
        #     # 빈 청크 제거
        #     # response_parsed_data['splitted_lyrics'] = [chunk for chunk in final_rewrapped_lyrics if chunk.strip()]

        #     print("--- LLM 응답 후처리 결과 ---")
        #     print(response_parsed_data.get('splitted_lyrics', []))
        #     print("-----------------------------")

        #     results.append(response_parsed_data.get('splitted_lyrics', []))

        # except Exception as e:
        #     print(f"Error splitting lyrics for '{title}' with Gemini API or post-processing: {e}")
        #     lines = lyrics.split('\n')
        #     chunk_size = 5
        #     fallback_lyrics_pages = ["\n".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size) if "\n".join(lines[i:i + chunk_size]).strip()]
        #     if not fallback_lyrics_pages:
        #         fallback_lyrics_pages = ["가사 분할 중 오류 발생."]
        #     results.append({"title": title, "splitted_lyrics": fallback_lyrics_pages})
    
    return results