# core/tasks.py

from celery import shared_task
from celery.app.task import Task as TaskType # celery.app.task.Task 타입 힌트를 위해 Task 임포트

from django.conf import settings
from django.core.files import File
from django.utils import timezone
from datetime import date
import os
import json
import re

# LLM 함수 임포트
from utils.llm import split_lyrics_to_json # 가사 분할은 여전히 LLM 사용
# 성경 구절 가져오는 함수는 bible_text_parser.py에서 가져옴
from utils.bible_text_parser import get_bible_contents as get_local_bible_contents

from utils.crawl import crawl_lyrics
from utils.update_pptx import load_template, edit_text_field, add_lyrics_slides, add_ads_slides, add_bible_slides, save_presentation
from utils.get_datetime import get_sunday_text

# 모델 임포트
from core.models import PptTemplate, WorshipInfo, SongInfo, PptRequest


@shared_task(bind=True)
def generate_ppt_task(self: TaskType, worship_info_id: int):
    """
    예배 PPT를 생성하는 Celery 태스크.
    진행 상황을 PptRequest 모델에 업데이트합니다.
    """
    
    ppt_request = None
    try:
        ppt_request = PptRequest.objects.get(celery_task_id=self.request.id)

        ppt_request.status = 'processing'
        ppt_request.progress_message = "PPT 제작을 시작합니다..."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 5, 'message': ppt_request.progress_message})

        # 1. 필요한 데이터 가져오기
        worship_info = WorshipInfo.objects.get(id=worship_info_id)
        normal_songs = SongInfo.objects.filter(worship_info=worship_info, is_ending_song=False).order_by('order')
        ending_song = SongInfo.objects.filter(worship_info=worship_info, is_ending_song=True).first()

        active_template = PptTemplate.objects.filter(is_active=True).order_by('-created_at').first()
        if not active_template or not active_template.template_file:
            ppt_request.status = 'failed'
            ppt_request.progress_message = "오류: 활성화된 PPT 템플릿 파일이 존재하지 않습니다. 관리자에게 문의하세요."
            ppt_request.save()
            self.update_state(state='FAILURE', meta={'progress': 0, 'message': ppt_request.progress_message})
            return {'status': 'failed', 'error': ppt_request.progress_message}
        
        template_file_path = active_template.template_file.path
        
        prs = load_template(template_file_path)
        cumulative_added_slide_count = 0

        # 2. 표지 수정
        next_sunday_text = get_sunday_text(worship_info.worship_date)
        prs = edit_text_field(prs=prs, slide_index=0, is_title=True, new_text=next_sunday_text)
        ppt_request.progress_message = "표지를 업데이트 중입니다..."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': ppt_request.progress_message})

        # 3. 예배 정보 필드 (기도자, 봉헌자, 광고 책임자, 성경봉독 범위, 설교자, 축도자) 수정
        SLIDE_INDEX_PRAYER = 14
        SLIDE_INDEX_OFFERING = 15
        SLIDE_INDEX_ADS_MANAGER = 18 # core/models.py 필드명과 일치
        SLIDE_INDEX_BIBLE_RANGE = 21
        SLIDE_INDEX_SERMON_TITLE = 23
        SLIDE_INDEX_ENDING_SONG_TITLE_TEMPLATE = 27
        SLIDE_INDEX_BENEDICTION_MINISTER = 37

        prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_PRAYER, is_title=True, new_text=worship_info.prayer_minister)
        prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_OFFERING, is_title=True, new_text=worship_info.offering_minister)
        prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_ADS_MANAGER, is_title=True, new_text=worship_info.ads_manager) # models.py 필드명 사용
        prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_BIBLE_RANGE, is_title=True, new_text=worship_info.sermon_scripture)
        prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_SERMON_TITLE, is_title=True, new_text=worship_info.sermon_title)
        prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_BENEDICTION_MINISTER, is_title=True, new_text=worship_info.benediction_minister) # models.py 필드명 사용

        ppt_request.progress_message = "예배 기본 정보를 슬라이드에 반영 중입니다..."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': ppt_request.progress_message})
        
        # 4. 찬양 파트 수정 (일반 찬양)
        songs_data_for_ppt = []
        for song in normal_songs:
            current_lyrics = song.lyrics
            current_lyrics_pages = song.lyrics_pages

            if not current_lyrics and song.source_url:
                ppt_request.progress_message = f"'{song.title}' 가사를 크롤링 중입니다..."
                ppt_request.save()
                self.update_state(state='PROGRESS', meta={'progress': 30, 'message': ppt_request.progress_message})
                current_lyrics = crawl_lyrics(song.source_url)
                if current_lyrics:
                    song.lyrics = current_lyrics
                    song.save()
                else:
                    ppt_request.progress_message = f"'{song.title}' 가사 크롤링 실패. 기본값 사용."
                    ppt_request.save()
                    current_lyrics = "가사를 찾을 수 없습니다."

            # 가사 분할 (이제 LLM_split_lyrics_to_json 사용)
            if song.lyrics and song.lyrics != "가사를 가져올 수 없습니다.":
                ppt_request.progress_message = f"'{song.title}' 가사를 AI로 분할 중입니다..."
                ppt_request.save()
                self.update_state(state='PROGRESS', meta={'progress': 40, 'message': ppt_request.progress_message})
                
                # LLM 연동 활성화: utils.llm.split_lyrics_to_json 호출
                splitted_res = split_lyrics_to_json([{"title": song.title, "lyrics": song.lyrics}])
                
                if splitted_res and splitted_res[0].get("splitted_lyrics"):
                    song.lyrics_pages = splitted_res[0]["splitted_lyrics"]
                    song.save()
                else:
                    ppt_request.progress_message = f"'{song.title}' 가사 분할 실패. 전체 가사 사용."
                    ppt_request.save()
                    song.lyrics_pages = [song.lyrics]
                    song.save()
            elif not song.lyrics_pages:
                song.lyrics_pages = ["가사를 가져올 수 없습니다."]
                song.save()

            songs_data_for_ppt.append({
                "title": song.title,
                "splitted_lyrics": song.lyrics_pages
            })
        
        SLIDE_INDEX_START_SONG = 5
        SLIDE_INDEX_LYRICS_TEMPLATE = 6
        
        for index, song_data in enumerate(songs_data_for_ppt):
            song_title = song_data["title"]
            splited_lyrics = song_data["splitted_lyrics"]

            ppt_request.progress_message = f"'{song_title}' 찬양 슬라이드 생성 중 ({index + 1}/{len(songs_data_for_ppt)})..."
            ppt_request.save()
            self.update_state(state='PROGRESS', meta={'progress': 50 + index * 5, 'message': ppt_request.progress_message})

            # 찬양 제목 슬라이드 수정 (기준 인덱스 + 현재까지 추가된 슬라이드 수)
            prs = edit_text_field(
                prs=prs,
                slide_index=SLIDE_INDEX_START_SONG + index * 2 + cumulative_added_slide_count,
                is_title=True,
                new_text=song_title
            )
            # 가사 슬라이드 추가 (기준 인덱스 + 1 + 현재까지 추가된 슬라이드 수)
            added_res = add_lyrics_slides(
                prs=prs,
                duplicate_slide_index=SLIDE_INDEX_LYRICS_TEMPLATE + index * 2 + cumulative_added_slide_count,
                slide_texts=splited_lyrics
            )
            prs = added_res["prs"]
            cumulative_added_slide_count += added_res["added_slide_count"]
        
        ppt_request.progress_message = "모든 찬양 슬라이드 생성을 완료했습니다."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 70, 'message': ppt_request.progress_message})

        # 5. 광고 페이지 추가
        ads_from_db = worship_info.worship_announcements
        if ads_from_db:
            SLIDE_INDEX_ADS_CONTENTS_TEMPLATE = 20
            added_ads_count = add_ads_slides(prs, ads_from_db, SLIDE_INDEX_ADS_CONTENTS_TEMPLATE + cumulative_added_slide_count)
            cumulative_added_slide_count += added_ads_count
        
        ppt_request.progress_message = "광고 슬라이드를 추가 중입니다..."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 80, 'message': ppt_request.progress_message})


        # 6. 성경봉독 슬라이드 추가
        # Sermon Scripture를 파싱하여 get_local_bible_contents에 전달
        scripture = worship_info.sermon_scripture # 폼에서 이미 유효성 검사되었으므로 파싱 로직 단순화
        
        # Regex to parse "책이름 장:절 - 장:절" or "책이름 장:절"
        pattern = re.compile(r'^\s*(.+?)\s*(\d+):(\d+)\s*(?:-\s*(?:(.+?)\s*)?(\d+):(\d+))?\s*$')
        match = pattern.match(scripture)

        if match:
            start_book = match.group(1).strip()
            start_ch = int(match.group(2))
            start_verse = int(match.group(3))
            
            end_book = match.group(4) # Can be None
            end_ch = int(match.group(5)) if match.group(5) else start_ch
            end_verse = int(match.group(6)) if match.group(6) else start_verse
            
            bible_contents = get_local_bible_contents(start_book, start_ch, start_verse, end_ch, end_verse)
        else:
            # 이 else 블록은 clean_sermon_scripture에서 이미 걸러지지만, 안전을 위해 남겨둠
            bible_contents = [{"title": "성경 본문", "contents": "성경 구절 형식이 올바르지 않아 내용을 가져올 수 없습니다."}]

        SLIDE_INDEX_BIBLE_CONTENTS_TEMPLATE = 22
        added_bible_count = add_bible_slides(prs, bible_contents, SLIDE_INDEX_BIBLE_CONTENTS_TEMPLATE + cumulative_added_slide_count)
        cumulative_added_slide_count += added_bible_count
        
        ppt_request.progress_message = "성경 말씀 슬라이드를 추가 중입니다..."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 85, 'message': ppt_request.progress_message})


        # 7. 결단 찬양 수정
        if ending_song:
            prs = edit_text_field(prs=prs, slide_index=SLIDE_INDEX_ENDING_SONG_TITLE_TEMPLATE + cumulative_added_slide_count, is_title=True, new_text=ending_song.title)

            current_lyrics = ending_song.lyrics
            current_lyrics_pages = ending_song.lyrics_pages
            
            if not current_lyrics and ending_song.source_url:
                ppt_request.progress_message = f"'{ending_song.title}' 가사를 크롤링 중입니다..."
                ppt_request.save()
                self.update_state(state='PROGRESS', meta={'progress': 90, 'message': ppt_request.progress_message})
                current_lyrics = crawl_lyrics(ending_song.source_url)
                if current_lyrics:
                    ending_song.lyrics = current_lyrics
                    ending_song.save()
                else:
                    current_lyrics = "가사를 찾을 수 없습니다."

            if not current_lyrics_pages and current_lyrics:
                ppt_request.progress_message = f"'{ending_song.title}' 가사를 AI로 분할 중입니다..."
                ppt_request.save()
                self.update_state(state='PROGRESS', meta={'progress': 92, 'message': ppt_request.progress_message})
                # LLM 연동 활성화: utils.llm.split_lyrics_to_json 호출
                splitted_res = split_lyrics_to_json([{"title": ending_song.title, "lyrics": ending_song.lyrics}])
                
                if splitted_res and splitted_res[0].get("splitted_lyrics"):
                    ending_song.lyrics_pages = splitted_res[0]["splitted_lyrics"]
                    ending_song.save()
                else:
                    ppt_request.progress_message = f"'{ending_song.title}' 가사 분할 실패. 전체 가사 사용."
                    ppt_request.save()
                    ending_song.lyrics_pages = [ending_song.lyrics]
                    ending_song.save()
            elif not ending_song.lyrics_pages:
                ending_song.lyrics_pages = ["가사를 가져올 수 없습니다."]
                ending_song.save()

            added_slide_res = add_lyrics_slides(
                prs=prs,
                duplicate_slide_index=SLIDE_INDEX_ENDING_SONG_TITLE_TEMPLATE + 1 + cumulative_added_slide_count,
                slide_texts=current_lyrics_pages
            )
            prs = added_slide_res["prs"]
            cumulative_added_slide_count += added_slide_res["added_slide_count"]

        ppt_request.progress_message = "결단 찬양 슬라이드 생성을 완료했습니다."
        ppt_request.save()
        self.update_state(state='PROGRESS', meta={'progress': 95, 'message': ppt_request.progress_message})


        # 8. 최종 PPT 저장
        generated_ppt_dir = os.path.join(settings.MEDIA_ROOT, 'generated_ppts')
        os.makedirs(generated_ppt_dir, exist_ok=True)

        worship_type_slug = worship_info.get_worship_type_display().replace(' ', '_').replace('(', '').replace(')', '')
        file_name = f"{worship_info.worship_date.strftime('%Y%m%d')}_{worship_type_slug}.pptx"
        full_save_path = os.path.join(generated_ppt_dir, file_name)
        
        save_presentation(prs, full_save_path)

        # 9. PptRequest 모델 업데이트 (파일 경로 및 상태)
        ppt_request.generated_ppt_file.name = os.path.join('generated_ppts', file_name)
        
        ppt_request.status = 'completed'
        ppt_request.progress_message = "PPT 제작이 완료되었습니다. 파일을 다운로드할 수 있습니다."
        ppt_request.completed_at = timezone.now()
        ppt_request.save()
        self.update_state(state='SUCCESS', meta={'progress': 100, 'message': ppt_request.progress_message, 'file_url': ppt_request.generated_ppt_file.url})

        return {'status': 'completed', 'file_url': ppt_request.generated_ppt_file.url}

    except WorshipInfo.DoesNotExist:
        error_message = "오류: 해당 예배 정보를 찾을 수 없습니다. PPT 제작 실패."
        print(error_message)
        if ppt_request:
            ppt_request.status = 'failed'
            ppt_request.progress_message = error_message
            ppt_request.save()
            self.update_state(state='FAILURE', meta={'message': error_message})
        return {'status': 'failed', 'error': error_message}
    except SongInfo.DoesNotExist:
        error_message = "오류: 해당 찬양 정보를 찾을 수 없습니다. PPT 제작 실패."
        print(error_message)
        if ppt_request:
            ppt_request.status = 'failed'
            ppt_request.progress_message = error_message
            ppt_request.save()
            self.update_state(state='FAILURE', meta={'message': error_message})
        return {'status': 'failed', 'error': error_message}
    except PptRequest.DoesNotExist:
        error_message = "오류: PPT 요청 객체를 찾을 수 없습니다. PPT 제작 실패."
        print(error_message)
        self.update_state(state='FAILURE', meta={'message': error_message})
        return {'status': 'failed', 'error': error_message}
    except (ValueError, FileNotFoundError) as e:
        error_message = f"성경 파일 또는 구절 파싱 오류: {e}"
        print(error_message)
        if ppt_request:
            ppt_request.status = 'failed'
            ppt_request.progress_message = error_message
            ppt_request.save()
            self.update_state(state='FAILURE', meta={'message': error_message})
        return {'status': 'failed', 'error': error_message}
    except Exception as e:
        error_message = f"PPT 제작 중 예상치 못한 오류 발생: {e}"
        print(error_message)
        import traceback
        traceback.print_exc()
        if ppt_request:
            ppt_request.status = 'failed'
            ppt_request.progress_message = error_message
            ppt_request.save()
            self.update_state(state='FAILURE', meta={'message': error_message})
        return {'status': 'failed', 'error': error_message}