# tests/test_bible_parser.py

import os
import sys
import shutil
import re

# Django settings 모킹을 위한 임시 클래스 정의
class MockSettings:
    def __init__(self, base_dir):
        self.BASE_DIR = base_dir

# 임시 테스트 환경 설정
# 현재 스크립트의 위치가 '프로젝트루트/tests/'이므로, BASE_DIR을 한 단계 위로 설정
TEST_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_temp_project')
TEST_BIBLE_TEXT_DIR = os.path.join(TEST_BASE_DIR, 'core', 'data', 'bible_text')
SAMPLE_BIBLE_FILE_NAME = "1-01창세기.txt"
SAMPLE_BIBLE_FILE_PATH = os.path.join(TEST_BIBLE_TEXT_DIR, SAMPLE_BIBLE_FILE_NAME)

# 임시 성경 텍스트 파일 내용
SAMPLE_BIBLE_CONTENT = """
창1:1 <천지 창조> 태초에 하나님이 천지를 창조하시니라
창1:2 땅이 혼돈하고 공허하며 흑암이 깊음 위에 있고 하나님의 영은 수면 위에 운행하시니라
창1:3 하나님이 이르시되 빛이 있으라 하시니 빛이 있었고
창1:4 빛이 하나님이 보시기에 좋았더라 하나님이 빛과 어둠을 나누사
창1:5 하나님이 빛을 낮이라 부르시고 어둠을 밤이라 부르시니라 저녁이 되고 아침이 되니 이는 첫째 날이니라
창1:6 하나님이 이르시되 물 가운데에 궁창이 있어 물과 물로 나뉘라 하시고
창1:7 하나님이 궁창을 만드사 궁창 아래의 물과 궁창 위의 물로 나뉘게 하시니 그대로 되니라
창1:8 하나님이 궁창을 하늘이라 부르시니라 저녁이 되고 아침이 되니 이는 둘째 날이니라
창2:1 천지와 만물이 다 이루어지니라
창2:2 하나님이 그가 하시던 일을 일곱째 날에 마치시니 그가 하시던 모든 일을 그치고 일곱째 날에 안식하시니라
창2:3 하나님이 그 일곱째 날을 복되게 하사 거룩하게 하셨으니 이는 하나님이 그 창조하시며 만드시던 모든 일을 마치시고 이 날에 안식하셨음이니라
창2:4 이것이 천지가 창조될 때에 하늘과 땅의 내력이니라 여호와 하나님이 땅과 하늘을 만드시던 날에
"""

def setup_test_environment():
    """테스트를 위한 임시 디렉토리 및 파일을 생성합니다."""
    print("Setting up test environment...")
    os.makedirs(TEST_BIBLE_TEXT_DIR, exist_ok=True)
    with open(SAMPLE_BIBLE_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(SAMPLE_BIBLE_CONTENT.strip())
    
    sys.modules['django.conf'] = type('module', (object,), {'settings': MockSettings(TEST_BASE_DIR)})

def cleanup_test_environment():
    """테스트 후 임시 디렉토리 및 파일을 삭제합니다."""
    print("Cleaning up test environment...")
    if os.path.exists(TEST_BASE_DIR):
        shutil.rmtree(TEST_BASE_DIR)
    if 'django.conf' in sys.modules:
        del sys.modules['django.conf']


def run_tests():
    """bible_text_parser.py의 함수들을 테스트합니다."""
    
    # 프로젝트의 루트 디렉토리를 sys.path에 추가하여 모듈 임포트 가능하게 함
    # 현재 스크립트가 tests/ 안에 있으므로, sys.path에 추가할 경로는 tests/의 부모 디렉토리
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path: # utils_path 대신 project_root를 추가
        sys.path.insert(0, project_root)
    
    # original_bible_file_map_genesis 변수 초기화
    original_bible_file_map_genesis = None # UnboundLocalError 해결
    
    try:
        # 이제 'utils' 패키지 내의 모듈로 임포트
        from utils.bible_text_parser import parse_verse_line, get_bible_contents, BIBLE_FILE_MAP, BIBLE_TEXT_DIR, VERSE_LINE_PATTERN, SECTION_TITLE_PATTERN

        # BIBLE_FILE_MAP이 테스트 환경에 맞게 조정될 때 원본 값 백업
        original_bible_file_map_genesis = BIBLE_FILE_MAP.get("창세기")
        BIBLE_FILE_MAP["창세기"] = SAMPLE_BIBLE_FILE_NAME
        
        # BIBLE_TEXT_DIR이 모킹된 경로를 가리키는지 확인 (setup_test_environment에서 설정)
        assert BIBLE_TEXT_DIR == TEST_BIBLE_TEXT_DIR

        print("\n--- Testing parse_verse_line ---")
        line1 = "창1:1 <천지 창조> 태초에 하나님이 천지를 창조하시니라"
        result1 = parse_verse_line(line1, "창세기")
        print(f"Input: '{line1}'")
        print(f"Output: {result1}")
        assert result1 == {
            "title": "창세기 1:1",
            "chapter": 1,
            "verse": 1,
            "contents": "태초에 하나님이 천지를 창조하시니라"
        }
        print("parse_verse_line Test 1 Passed!")

        line2 = "창1:2 땅이 혼돈하고 공허하며 흑암이 깊음 위에 있고 하나님의 영은 수면 위에 운행하시니라"
        result2 = parse_verse_line(line2, "창세기")
        print(f"Input: '{line2}'")
        print(f"Output: {result2}")
        assert result2 == {
            "title": "창세기 1:2",
            "chapter": 1,
            "verse": 2,
            "contents": "땅이 혼돈하고 공허하며 흑암이 깊음 위에 있고 하나님의 영은 수면 위에 운행하시니라"
        }
        print("parse_verse_line Test 2 Passed!")

        line3 = "잘못된 구절 형식입니다."
        result3 = parse_verse_line(line3, "창세기")
        print(f"Input: '{line3}'")
        print(f"Output: {result3}")
        assert result3 is None
        print("parse_verse_line Test 3 Passed!")


        print("\n--- Testing get_bible_contents ---")
        
        print("\n--- Test 4: Single verse (창1:1) ---")
        verses4 = get_bible_contents("창세기", 1, 1, 1, 1)
        print(f"Retrieved {len(verses4)} verses.")
        assert len(verses4) == 1
        assert verses4[0]["title"] == "창세기 1:1"
        assert verses4[0]["contents"] == "태초에 하나님이 천지를 창조하시니라"
        print("get_bible_contents Test 4 Passed!")

        print("\n--- Test 5: Multiple verses in same chapter (창1:3-5) ---")
        verses5 = get_bible_contents("창세기", 1, 3, 1, 5)
        print(f"Retrieved {len(verses5)} verses.")
        assert len(verses5) == 3
        assert verses5[0]["title"] == "창세기 1:3"
        assert verses5[2]["title"] == "창세기 1:5"
        print("get_bible_contents Test 5 Passed!")

        print("\n--- Test 6: Multiple verses across chapters (창1:7 - 창2:2) ---")
        verses6 = get_bible_contents("창세기", 1, 7, 2, 2)
        print(f"Retrieved {len(verses6)} verses.")
        assert len(verses6) == 4
        assert verses6[0]["title"] == "창세기 1:7"
        assert verses6[1]["title"] == "창세기 1:8"
        assert verses6[2]["title"] == "창세기 2:1"
        assert verses6[3]["title"] == "창세기 2:2"
        print("get_bible_contents Test 6 Passed!")

        print("\n--- Test 7: Non-existent Bible book ---")
        try:
            get_bible_contents("가짜책", 1, 1, 1, 1)
            assert False, "ValueError was not raised for non-existent book."
        except ValueError as e:
            print(f"Caught expected error: {e}")
            assert "파일 정보를 찾을 수 없습니다" in str(e)
        print("get_bible_contents Test 7 Passed!")

        print("\n--- Test 8: Non-existent file (mapped but not present) ---")
        BIBLE_FILE_MAP["가짜책2"] = "non_existent_file.txt"
        try:
            get_bible_contents("가짜책2", 1, 1, 1, 1)
            assert False, "FileNotFoundError was not raised for non-existent file."
        except FileNotFoundError as e:
            print(f"Caught expected error: {e}")
            assert "파일을 찾을 수 없습니다" in str(e)
        print("get_bible_contents Test 8 Passed!")
        del BIBLE_FILE_MAP["가짜책2"]

        print("\n--- Test 9: Range not found in file (e.g., very high chapter) ---")
        try:
            get_bible_contents("창세기", 99, 1, 99, 5)
            assert False, "ValueError was not raised for out-of-range request."
        except ValueError as e:
            print(f"Caught expected error: {e}")
            assert "파일에서 찾을 수 없거나 범위가 잘못되었습니다" in str(e)
        print("get_bible_contents Test 9 Passed!")

        print("\n--- Test 10: Start range after end range ---")
        try:
            get_bible_contents("창세기", 1, 5, 1, 3)
            assert False, "ValueError was not raised for invalid range."
        except ValueError as e:
            print(f"Caught expected error: {e}")
            assert "파일에서 찾을 수 없거나 범위가 잘못되었습니다" in str(e)
        print("get_bible_contents Test 10 Passed!")


    except Exception as e:
        print(f"\nAn unexpected error occurred during tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # BIBLE_FILE_MAP 복원
        if original_bible_file_map_genesis is not None:
             BIBLE_FILE_MAP["창세기"] = original_bible_file_map_genesis
        else: # 원래 '창세기' 키가 없었다면 제거
             if "창세기" in BIBLE_FILE_MAP:
                 del BIBLE_FILE_MAP["창세기"]

        # sys.path에서 추가된 경로 제거 (project_root를 제거)
        if project_root in sys.path:
            sys.path.remove(project_root)


if __name__ == "__main__":
    try:
        setup_test_environment()
        run_tests()
    finally:
        cleanup_test_environment()

    print("\n--- All tests attempted. Check logs for 'Passed!' messages. ---")

