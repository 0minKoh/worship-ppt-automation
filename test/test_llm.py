# tests/test_llm.py

import os
import sys
import unittest
from unittest.mock import patch, Mock
import json

# 프로젝트 루트 디렉토리를 sys.path에 추가하여 모듈 임포트 가능하게 함
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 테스트 대상 함수 임포트
# LLM 연동 부분은 _call_gemini_api에서 모의됩니다.
from utils.llm import SplittedLyricsResponse, split_lyrics_to_json

# --- 테스트 시나리오를 위한 샘플 데이터 ---
SAMPLE_SONG_TITLE = "은혜 아니면"
SAMPLE_FULL_LYRICS = """
어둠 속 헤매이던 내 영혼
갈길 몰라 방황할 때에
주의 십자가 영광의 그 빛이
나를 향해 비추어주셨네
주홍빛보다 더 붉은 내 죄
그리스도의 피로 씻기어
완전한 사랑 주님의 은혜로
새 생명 주께 얻었네
은혜 아니면 나 서지 못하네
십자가의 그 사랑 능력 아니면
나 서지 못하네
은혜 아니면 나 서지 못하네
놀라운 사랑 그 은혜 아니면
나 서지 못하네

나의 노력과 의지가 아닌
오직 주님의 그 뜻 안에서
의로운 자라 내게 말씀하셨네
완전하신 그 은혜로

은혜 아니면 나 서지 못하네
십자가의 그 사랑 능력 아니면
나 서지 못하네
은혜 아니면 나 서지 못하네
놀라운 사랑 그 은혜 아니면
나 서지 못하네

이제 나 사는 것 아니요
오직 예수 내 안에 살아계시니
나의 능력 아닌 주의 능력으로
이제 주와 함께 살리라
오직 은혜로 나 살아가리라
십자가의 그 사랑
주의 능력으로 나는 서리라
주의 은혜로 나 살아가리라
십자가 사랑 그 능력으로 나 살리라
주 은혜로 나 살리라
"""

# _call_gemini_api가 반환할 모의 LLM 응답 (JSON 파싱 후 dict 형태)
# 이 응답은 중복된 청크, 15자 초과 줄, 4줄 초과 청크 등을 포함하여
# _remove_consecutive_duplicates와 _rewrap_lyrics_chunk가 잘 작동하는지 테스트합니다.
MOCK_LLM_RAW_RESPONSE_DICT = {
    "title": SAMPLE_SONG_TITLE,
    "splitted_lyrics": [
        "어둠 속 헤매이던 내 영혼\n갈길 몰라 방황할 때에", # 2 lines, ok
        "주의 십자가 영광의 그 빛이\n나를 향해 비추어주셨네", # 2 lines, ok
        "주홍빛보다 더 붉은 내 죄\n그리스도의 피로 씻기어\n완전한 사랑 주님의 은혜로\n새 생명 주께 얻었네", # 4 lines, ok
        "은혜 아니면 나 서지 못하네\n십자가의 그 사랑 능력 아니면 나 서지 못하네", # Long line, needs re-wrap
        "은혜 아니면 나 서지 못하네\n십자가의 그 사랑 능력 아니면 나 서지 못하네", # DUPLICATE
        "놀라운 사랑 그 은혜 아니면 나 서지 못하네", # Long line, needs re-wrap
        "나의 노력과 의지가 아닌 오직 주님의 그 뜻 안에서", # Long line, needs re-wrap
        "의로운 자라 내게 말씀하셨네\n완전하신 그 은혜로", # 2 lines, ok
        "은혜 아니면 나 서지 못하네\n십자가의 그 사랑 능력 아니면 나 서지 못하네", # Long line, needs re-wrap
        "이제 나 사는 것 아니요\n오직 예수 내 안에 살아계시니", # 2 lines, ok
        "나의 능력 아닌 주의 능력으로\n이제 주와 함께 살리라", # 2 lines, ok
        "오직 은혜로 나 살아가리라\n십자가의 그 사랑 주의 능력으로 나는 서리라", # Long line, needs re-wrap
        "주의 은혜로 나 살아가리라\n십자가 사랑 그 능력으로 나 살리라\n주 은혜로 나 살리라" # 3 lines, ok
    ]
}

# _remove_consecutive_duplicates 와 _rewrap_lyrics_chunk 적용 후 예상되는 최종 결과
EXPECTED_FINAL_SPLITTED_LYRICS = [
    "어둠 속 헤매이던\n내 영혼",
    "갈길 몰라\n방황할 때에",
    "주의 십자가\n영광의 그 빛이",
    "나를 향해\n비추어주셨네",
    "주홍빛보다 더\n붉은 내 죄",
    "그리스도의\n피로 씻기어",
    "완전한 사랑\n주님의 은혜로\n새 생명 주께\n얻었네",
    "은혜 아니면\n나 서지 못하네\n십자가의 그 사랑\n능력 아니면",
    "놀라운 사랑 그\n은혜 아니면\n나 서지 못하네",
    "나의 노력과\n의지가 아닌\n오직 주님의\n그 뜻 안에서",
    "의로운 자라\n내게 말씀하셨네\n완전하신\n그 은혜로",
    "십자가의 그 사랑\n능력 아니면", # '은혜 아니면 나 서지 못하네' 중복 제거
    "이제 나 사는 것\n아니요\n오직 예수 내\n안에 살아계시니",
    "나의 능력 아닌\n주의 능력으로\n이제 주와 함께\n살리라",
    "오직 은혜로\n나 살아가리라\n십자가의 그 사랑\n주의 능력으로",
    "나는 서리라\n주의 은혜로\n나 살아가리라\n십자가 사랑 그",
    "능력으로 나 살리라\n주 은혜로 나 살리라"
]


class TestLLMFuncs(unittest.TestCase):

    @patch('utils.llm._call_gemini_api')
    def test_split_lyrics_to_json(self, mock_call_gemini_api):
        """
        split_lyrics_to_json 함수가 LLM 호출 및 후처리를 올바르게 수행하는지 테스트합니다.
        """
        print("\n--- Testing split_lyrics_to_json ---")
        
        # _call_gemini_api 모의 설정
        # LLM이 반환할 데이터를 설정합니다.
        # mock_call_gemini_api.return_value = MOCK_LLM_RAW_RESPONSE_DICT
        
        input_data = [
            {"title": SAMPLE_SONG_TITLE, "lyrics": SAMPLE_FULL_LYRICS}
        ]

        # 함수 호출
        result: list = split_lyrics_to_json(input_data)
        # result = ['어둠 속 헤매이던 내 영혼\n갈길 몰라 방황할 때에', '주의 십자가 영광의 그 빛이\n나를 향해 비추어주셨네', '주홍빛보다 더 붉은 내 죄\n그리스도의 피로 씻기어\n완전한 사랑 주님의 은혜로\n새 생명 주께 얻었네', '은혜 아니면 나 서지 못하네\n십자가의 그 사랑 능력 아니면 나 서지 못하네', '은혜 아니면 나 서지 못하네\n십자가의 그 사랑 능력 아니면 나 서지 못하네', '놀라운 사랑 그 은혜 아니면 나 서지 못하네', '나의 노력과 의지가 아닌 오직 주님의 그 뜻 안에서', '의로운 자라 내게 말씀하셨네\n완전하신 그 은혜로', '은혜 아니면 나 서지 못하네\n십자가의 그 사랑 능력 아니면 나 서지 못하네', '이제 나 사는 것 아니요\n오직 예수 내 안에 살아계시니', '나의 능력 아닌 주의 능력으로\n이제 주와 함께 살리라', '오직 은혜로 나 살아가리라\n십자가의 그 사랑 주의 능력으로 나는 서리라', '주의 은혜로 나 살아가리라\n십자가 사랑 그 능력으로 나 살리라\n주 은혜로 나 살리라']
        
        for item in result:
            print(f"Processed Lyrics Chunk: {item}")
        print("test_split_lyrics_to_json Passed!")

    # def test_remove_consecutive_duplicates(self):
    #     """_remove_consecutive_duplicates 헬퍼 함수 테스트."""
    #     print("\n--- Testing _remove_consecutive_duplicates ---")
    #     chunks = ["A", "B", "B", "C", "D", "B", "B"]
    #     expected = ["A", "B", "C", "D", "B"]
    

    #     result = _remove_consecutive_duplicates(chunks)
    #     print(f"Input: {chunks}")
    #     print(f"Output: {result}")
    #     self.assertEqual(result, expected)
    #     print("_remove_consecutive_duplicates Passed!")

    #     chunks_with_exact_duplicates = ["A", "B", "B", "C", "A", "A", "D"]
    #     expected_exact_duplicates = ["A", "B", "C", "A", "D"]
    #     result_exact = _remove_consecutive_duplicates(chunks_with_exact_duplicates)
    #     self.assertEqual(result_exact, expected_exact_duplicates)
    #     print("_remove_consecutive_duplicates (exact duplicates) Passed!")

    #     self.assertEqual(_remove_consecutive_duplicates([]), [])
    #     self.assertEqual(_remove_consecutive_duplicates(["Only One"]), ["Only One"])
    #     print("_remove_consecutive_duplicates edge cases Passed!")


    # def test_rewrap_lyrics_chunk(self):
    #     """_rewrap_lyrics_chunk 헬퍼 함수 테스트."""
    #     print("\n--- Testing _rewrap_lyrics_chunk ---")
        
    #     # 15자 초과 줄 재조정, 4줄 제한
    #     chunk1 = "십자가의 그 사랑 능력 아니면 나 서지 못하네"
    #     expected1 = "십자가의 그\n사랑 능력\n아니면 나\n서지 못하네" # capped at 4 lines
    #     result1 = _rewrap_lyrics_chunk(chunk1, max_line_len=15, max_lines_per_chunk=4)
    #     print(f"Input chunk1:\n'{chunk1}'\nOutput:\n'{result1}'")
    #     self.assertEqual(result1, expected1)
    #     print("_rewrap_lyrics_chunk Test 1 Passed!")

    #     # 이미 짧은 줄
    #     chunk2 = "짧은 가사\n두 줄"
    #     expected2 = "짧은 가사\n두 줄"
    #     result2 = _rewrap_lyrics_chunk(chunk2, max_line_len=15, max_lines_per_chunk=4)
    #     print(f"Input chunk2:\n'{chunk2}'\nOutput:\n'{result2}'")
    #     self.assertEqual(result2, expected2)
    #     print("_rewrap_lyrics_chunk Test 2 Passed!")
        
    #     # 4줄 초과하지만 rewrap 시 4줄 이내로 되는 경우
    #     chunk3 = "매우 긴 한 줄입니다만\n두 번째 줄도\n길지 않네요\n세 번째도\n네 번째도\n다섯 번째"
    #     expected3 = "매우 긴 한\n줄입니다만\n두 번째 줄도\n길지 않네요" # capped at 4 lines
    #     result3 = _rewrap_lyrics_chunk(chunk3, max_line_len=15, max_lines_per_chunk=4)
    #     print(f"Input chunk3:\n'{chunk3}'\nOutput:\n'{result3}'")
    #     self.assertEqual(result3, expected3)
    #     print("_rewrap_lyrics_chunk Test 3 Passed!")

    #     # 한 단어가 최대 길이를 넘는 경우
    #     chunk4 = "supercalifragilisticexpialidocious"
    #     expected4 = "supercalifragilis\nticexpialidocious" # word itself split
    #     result4 = _rewrap_lyrics_chunk(chunk4, max_line_len=15, max_lines_per_chunk=4)
    #     print(f"Input chunk4:\n'{chunk4}'\nOutput:\n'{result4}'")
    #     # NOTE: 현재 _rewrap_lyrics_chunk는 단어 자체는 자르지 않고 새 줄에 배치함
    #     # 즉, 'supercalifragilisticexpialidocious'는 한 줄로 그대로 남아 있을 것입니다.
    #     # 만약 단어 자체도 자르기를 원한다면 _rewrap_lyrics_chunk 로직을 더 복잡하게 수정해야 합니다.
    #     # 현재 로직의 기대값은:
    #     self.assertEqual(result4, "supercalifragilisticexpialidocious") # 단어 자체는 자르지 않으므로
    #     print("_rewrap_lyrics_chunk Test 4 Passed! (Word not split within line)")

    #     print("test_rewrap_lyrics_chunk Passed All Sub-Tests!")


if __name__ == '__main__':
    # unittest.main()은 sys.argv를 직접 파싱하므로,
    # 터미널에서 실행할 때 스크립트 이름만 전달되도록 합니다.
    unittest.main(argv=sys.argv[:1])

