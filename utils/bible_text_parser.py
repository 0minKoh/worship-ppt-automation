# utils/bible_text_parser.py

import os
import re
from django.conf import settings # Django settings에 접근하여 BASE_DIR 가져오기

# 성경 TXT 파일들이 저장된 디렉토리 경로
# settings.BASE_DIR은 Django 프로젝트의 루트 디렉토리를 가리킵니다.
BIBLE_TEXT_DIR = os.path.join(settings.BASE_DIR, 'core', 'data', 'bible_text')

# 성경책 전체 이름과 파일 이름 매핑
# 이 매핑은 당신이 가진 성경 TXT 파일의 이름과 정확히 일치해야 합니다.
# 예시이며, 실제 모든 66권에 대해 채워주셔야 합니다.
BIBLE_FILE_MAP = {
    "창세기": "1-01창세기.txt",
    "출애굽기": "1-02출애굽기.txt",
    "레위기": "1-03레위기.txt",
    "민수기": "1-04민수기.txt",
    "신명기": "1-05신명기.txt",
    "여호수아": "1-06여호수아.txt",
    "사사기": "1-07사사기.txt",
    "룻기": "1-08룻기.txt",
    "사무엘상": "1-09사무엘상.txt",
    "사무엘하": "1-10사무엘하.txt",
    "열왕기상": "1-11열왕기상.txt",
    "열왕기하": "1-12열왕기하.txt",
    "역대상": "1-13역대상.txt",
    "역대하": "1-14역대하.txt",
    "에스라": "1-15에스라.txt",
    "느헤미야": "1-16느헤미야.txt",
    "에스더": "1-17에스더.txt",
    "욥기": "1-18욥기.txt",
    "시편": "1-19시편.txt",
    "잠언": "1-20잠언.txt",
    "전도서": "1-21전도서.txt",
    "아가": "1-22아가.txt",
    "이사야": "1-23이사야.txt",
    "예레미야": "1-24예레미야.txt",
    "예레미야애가": "1-25예레미야애가.txt",
    "에스겔": "1-26에스겔.txt",
    "다니엘": "1-27다니엘.txt",
    "호세아": "1-28호세아.txt",
    "요엘": "1-29요엘.txt",
    "아모스": "1-30아모스.txt",
    "오바댜": "1-31오바댜.txt",
    "요나": "1-32요나.txt",
    "미가": "1-33미가.txt",
    "나훔": "1-34나훔.txt",
    "하박국": "1-35하박국.txt",
    "스바냐": "1-36스바냐.txt",
    "학개": "1-37학개.txt",
    "스가랴": "1-38스가랴.txt",
    "말라기": "1-39말라기.txt",
    "마태복음": "2-01마태복음.txt",
    "마가복음": "2-02마가복음.txt",
    "누가복음": "2-03누가복음.txt",
    "요한복음": "2-04요한복음.txt",
    "사도행전": "2-05사도행전.txt",
    "로마서": "2-06로마서.txt",
    "고린도전서": "2-07고린도전서.txt",
    "고린도후서": "2-08고린도후서.txt",
    "갈라디아서": "2-09갈라디아서.txt",
    "에베소서": "2-10에베소서.txt",
    "빌립보서": "2-11빌립보서.txt",
    "골로새서": "2-12골로새서.txt",
    "데살로니가전서": "2-13데살로니가전서.txt",
    "데살로니가후서": "2-14데살로니가후서.txt",
    "디모데전서": "2-15디모데전서.txt",
    "디모데후서": "2-16디모데후서.txt",
    "디도서": "2-17디도서.txt",
    "빌레몬서": "2-18빌레몬서.txt",
    "히브리서": "2-19히브리서.txt",
    "야고보서": "2-20야고보서.txt",
    "베드로전서": "2-21베드로전서.txt",
    "베드로후서": "2-22베드로후서.txt",
    "요한일서": "2-23요한일서.txt",
    "요한이서": "2-24요한이서.txt",
    "요한삼서": "2-25요한삼서.txt",
    "유다서": "2-26유다서.txt",
    "요한계시록": "2-27요한계시록.txt",
}

# 정규표현식: "책이름장:절 내용" 형태의 한 줄을 파싱합니다.
# Group 1: 책 이름 약어 (예: '창', '요')
# Group 2: 장 (예: '1')
# Group 3: 절 (예: '1')
# Group 4: 내용 (예: '<천지 창조> 태초에 하나님이 천지를 창조하시니라')
VERSE_LINE_PATTERN = re.compile(r'^(\S+?)(\d+):(\d+)\s+(.*)$')

# 정규표현식: 내용에서 "<천지 창조>"와 같은 섹션 제목을 제거합니다.
SECTION_TITLE_PATTERN = re.compile(r'<[^>]+>')

def parse_verse_line(line: str, full_book_name: str):
    """
    성경 텍스트 파일의 한 줄을 파싱하여 구절 정보와 내용을 추출합니다.
    """
    match = VERSE_LINE_PATTERN.match(line.strip())
    if match:
        book_abbr, ch_str, verse_str, content = match.groups()
        
        # 내용에서 <섹션 제목> 제거
        cleaned_content = SECTION_TITLE_PATTERN.sub('', content).strip()
        
        return {
            "title": f"{full_book_name} {ch_str}:{verse_str}", # 예: "창세기 1:1"
            "chapter": int(ch_str),
            "verse": int(verse_str),
            "contents": cleaned_content
        }
    return None

def get_bible_contents(bible_book: str, begin_ch: int, begin_verse: int, end_ch: int, end_verse: int) -> list:
    """
    로컬 TXT 파일에서 지정된 범위의 성경 구절 내용을 가져옵니다.
    """
    bible_file_name = BIBLE_FILE_MAP.get(bible_book)
    if not bible_file_name:
        raise ValueError(f"성경책 '{bible_book}'에 대한 파일 정보를 찾을 수 없습니다. 'utils/bible_text_parser.py'의 BIBLE_FILE_MAP을 확인하고 채워주세요.")
    
    file_path = os.path.join(BIBLE_TEXT_DIR, bible_file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"성경 파일 '{file_path}'를 찾을 수 없습니다. 'core/data/bible_text/' 폴더에 파일이 있고 이름이 정확한지 확인해주세요.")

    verses = []
    is_in_range = False # 구절 범위 시작 플래그

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parsed_line = parse_verse_line(line, bible_book)
            if not parsed_line:
                continue

            current_ch = parsed_line['chapter']
            current_verse = parsed_line['verse']
            
            # 범위 시작 조건
            if current_ch == begin_ch and current_verse == begin_verse:
                is_in_range = True
            
            # 범위 끝 조건
            if is_in_range:
                if current_ch == end_ch and current_verse > end_verse:
                    is_in_range = False # 범위 초과, 종료
            
            if is_in_range:
                verses.append({
                    "title": parsed_line['title'], # 예: "창1:1"
                    "contents": parsed_line['contents']
                })
            
            # 범위 끝을 넘어서면 더 이상 읽을 필요 없음 (최적화)
            if current_ch > end_ch and is_in_range:
                break # 다음 장으로 넘어갔고 이미 범위를 벗어났으면 중단

    if not verses:
        raise ValueError(f"성경 구절 '{bible_book} {begin_ch}:{begin_verse}-{end_ch}:{end_verse}'을 파일에서 찾을 수 없거나 범위가 잘못되었습니다.")
    
    return verses