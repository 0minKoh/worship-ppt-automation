# tests/test_bible_parser_local.py

import os
import sys
import unittest
from unittest.mock import patch, Mock

# --- 테스트 환경 설정 ---
# 이 테스트 파일이 '프로젝트루트/tests/' 안에 있다고 가정하고,
# 프로젝트 루트 디렉토리를 sys.path에 추가합니다.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Django settings를 모킹하여 BASE_DIR이 프로젝트 루트를 가리키도록 합니다.
# 이렇게 해야 bible_text_parser.py가 실제 성경 파일을 찾을 수 있습니다.
sys.modules['django.conf'] = Mock(settings=Mock(BASE_DIR=_project_root))

# 이제 테스트 대상 모듈을 임포트합니다.
# 이 시점에서 bible_text_parser.py는 모킹된 settings.BASE_DIR을 사용합니다.
from utils.bible_text_parser import get_bible_contents, BIBLE_FILE_MAP

class TestBibleTextParserLocal(unittest.TestCase):

    def test_get_bible_contents_from_local_file(self):
        """
        로컬 성경 TXT 파일에서 지정된 범위의 성경 구절 내용을 올바르게 가져오는지 테스트합니다.
        이 테스트를 실행하기 전에 'core/data/bible_text/' 폴더에
        실제 EUC-KR로 인코딩된 성경 TXT 파일들이 있어야 합니다.
        """
        print("\n--- Testing get_bible_contents from actual local files ---")
        
        # --- 테스트할 실제 성경 구절 범위 설정 ---
        # 이 값들은 당신의 'core/data/bible_text/1-01창세기.txt' 파일 내용과 일치해야 합니다.
        bible_book = "창세기"
        begin_ch = 1
        begin_verse = 1
        end_ch = 1
        end_verse = 5
        
        # NOTE: BIBLE_FILE_MAP은 utils/bible_text_parser.py에서 직접 가져오므로,
        # 해당 파일의 BIBLE_FILE_MAP이 정확히 완성되어 있어야 합니다.
        # 또한, 해당 맵에 지정된 파일명('1-01창세기.txt')이 'core/data/bible_text/' 폴더에 존재해야 합니다.

        try:
            verses = get_bible_contents(bible_book, begin_ch, begin_verse, end_ch, end_verse)
            
            print(f"Retrieved {len(verses)} verses for {bible_book} {begin_ch}:{begin_verse}-{end_ch}:{end_verse}")
            self.assertGreater(len(verses), 0) # 최소 1개 이상의 구절이 반환되어야 함
            
            # --- 구절 내용 검증 (실제 파일 내용 기반) ---
            # '창세기 1:1'의 실제 내용: '태초에 하나님이 천지를 창조하시니라'
            self.assertEqual(verses[0]["title"], "창세기 1:1")
            self.assertIn("천지를 창조하시니라", verses[0]["contents"])
            
            # '창세기 1:5'의 실제 내용: '하나님이 빛을 낮이라 부르시고 어둠을 밤이라 부르시니라 저녁이 되고 아침이 되니 이는 첫째 날이니라'
            self.assertEqual(verses[-1]["title"], "창세기 1:5")
            self.assertIn("이는 첫째 날이니라", verses[-1]["contents"])
            
            print(f"get_bible_contents from local file for {bible_book} {begin_ch}:{begin_verse}-{end_ch}:{end_verse} Passed!")

        except (ValueError, FileNotFoundError) as e:
            self.fail(f"Test failed due to expected file/range error: {e}")
        except Exception as e:
            self.fail(f"Test failed due to unexpected error: {e}")

    def test_get_bible_contents_multiple_chapters(self):
        """
        여러 장에 걸친 성경 구절을 올바르게 가져오는지 테스트합니다.
        '창세기 1:7 - 2:2' 범위는 SAMPLE_BIBLE_CONTENT에 존재합니다.
        """
        print("\n--- Test: Multiple verses across chapters (창1:7 - 창2:2) ---")
        bible_book = "창세기"
        begin_ch = 1
        begin_verse = 7
        end_ch = 2
        end_verse = 2

        try:
            verses = get_bible_contents(bible_book, begin_ch, begin_verse, end_ch, end_verse)
            print(f"Retrieved {len(verses)} verses for {bible_book} {begin_ch}:{begin_verse}-{end_ch}:{end_verse}")
            self.assertEqual(len(verses), 27) # 창1:7, 1:8, 2:1, 2:2
            self.assertEqual(verses[0]["title"], "창세기 1:7")
            self.assertIn("궁창을 만드사", verses[0]["contents"])
            self.assertEqual(verses[-1]["title"], "창세기 2:2")
            self.assertIn("일곱째 날에 안식하시니라", verses[-1]["contents"])
            print("get_bible_contents multiple chapters Passed!")
        except (ValueError, FileNotFoundError) as e:
            self.fail(f"Test failed for multiple chapters due to error: {e}")
        except Exception as e:
            self.fail(f"Test failed for multiple chapters due to unexpected error: {e}")


if __name__ == "__main__":
    unittest.main()

