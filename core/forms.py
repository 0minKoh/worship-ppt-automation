# core/forms.py

import json
import re
from django import forms
from .models import WorshipInfo, SongInfo
from django.forms import inlineformset_factory # SongInfo를 WorshipInfo와 함께 관리하기 위함
from django.forms import inlineformset_factory, BaseInlineFormSet # BaseInlineFormSet 임포트

class WorshipInfoForm(forms.ModelForm):
    """
    예배 정보 입력을 위한 폼.
    예배준비팀이 사용합니다.
    """
    class Meta:
        model = WorshipInfo
        # 사용자로부터 직접 입력받을 필드들을 명시합니다.
        # is_llm_processed는 LLM 처리 여부를 나타내므로 사용자가 직접 입력하지 않습니다.
        # created_by는 로그인한 사용자 정보로 자동 설정되므로 forms에 포함하지 않습니다.
        fields = [
            'worship_date', 'worship_type', 'speaker', 'sermon_title',
            'sermon_scripture', 'prayer_minister', 'offering_minister',
            'ads_manager',
            # 'main_prayer_topic',
            'worship_announcements',
            # 'notes',
        ]
        # 폼 필드에 대한 레이블을 설정하여 사용자에게 더 친숙하게 보여줍니다.
        labels = {
            'worship_date': '예배 날짜',
            'worship_type': '예배 종류',
            'speaker': '설교자',
            'sermon_title': '설교 제목',
            'sermon_scripture': '설교 본문 범위',
            'prayer_minister': '기도자',
            'offering_minister': '봉헌자',
            'ads_manager': '광고 담당자',
            'benediction_minister': '축도자',
            # 'main_prayer_topic': '예배 기도 제목',
            'worship_announcements': '광고 목록 (숨김)',
            # 'notes': '추가 비고',
        }
        # 위젯을 사용하여 폼 필드의 HTML 표현을 커스터마이징할 수 있습니다.
        widgets = {
            'worship_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}), # 날짜 선택기를 제공
            'worship_type': forms.Select(attrs={'class': 'form-select'}),
            'speaker': forms.TextInput(attrs={'class': 'form-input', 'value': '노진수 목사'}),
            'sermon_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 여호와가 누구이기에'}),
            'sermon_scripture': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 출애굽기 3:4 - 3:12'}),
            'prayer_minister': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 임현서 청년'}),
            'offering_minister': forms.TextInput(attrs={'class': 'form-input', 'value': '이현 청년'}),
            'ads_manager': forms.TextInput(attrs={'class': 'form-input', 'value': '노진수 목사'}),
            'benediction_minister': forms.TextInput(attrs={
                'class': 'form-input',
                'value': '노진수 목사',
            }),
            # 'main_prayer_topic': forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea hidden'}),
            'worship_announcements': forms.Textarea(attrs={'rows': 6, 'class': 'form-textarea announcements-json-field', 'placeholder': 'JSON 형식으로 입력하세요: [{"title": "광고1", "contents": "내용1"}, ...]'}),
            # 'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea hidden'}),
        }

    def clean_worship_announcements(self):
        """worship_announcements 필드의 JSON 유효성을 검사하고 Python 객체로 반환합니다."""
        data = self.cleaned_data.get('worship_announcements')
        
        # 데이터가 문자열이면 JSON 파싱 시도 (POST 요청 시 JavaScript에서 문자열화된 경우)
        if isinstance(data, str) and data: # 빈 문자열이 아닌 경우에만 파싱
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("유효한 JSON 형식으로 광고 목록을 입력해주세요.")
        # 데이터가 이미 리스트(Python 객체)이면 그대로 사용 (GET 요청 시 initial로 들어온 경우 등)
        elif isinstance(data, list):
            parsed_data = data
        else: # 데이터가 없거나 다른 타입이면 빈 리스트로 처리
            parsed_data = []

        # JSON 배열 형식 및 각 항목의 유효성 추가 검사
        if not isinstance(parsed_data, list):
            raise forms.ValidationError("광고 목록은 JSON 배열(리스트) 형식이어야 합니다.")
        
        # 각 항목이 'title'과 'contents'를 가진 딕셔너리인지 검사
        cleaned_announcements = []
        for item in parsed_data:
            if not isinstance(item, dict):
                raise forms.ValidationError("각 광고 항목은 객체(딕셔너리) 형식이어야 합니다.")
            
            title = item.get('title', '').strip()
            contents = item.get('contents', '').strip()

            # 제목과 내용 중 하나라도 값이 있는 항목만 유효한 광고로 간주
            if title or contents:
                cleaned_announcements.append({'title': title, 'contents': contents})
            # else: # 둘 다 비어있는 항목은 무시 (JavaScript 로직과 일치)
            #     pass

        return cleaned_announcements # 유효한 경우 정제된 Python 객체 반환
    
    # 성경 본문 범위 유효성 검증 메서드 추가
    def clean_sermon_scripture(self):
        scripture = self.cleaned_data.get('sermon_scripture')
        if not scripture:
            return scripture # 비어있는 필드는 필수 검증 (blank=False)에 맡김

        # "책이름 장:절 - 장:절" 또는 "책이름 장:절" 형식 검증
        # 예: "요한복음 3:16-18", "창세기 1:1"
        # 띄어쓰기 허용, 마지막 - 이후는 생략 가능 (단일 절 또는 장 전체)
        # 챕터와 절이 반드시 숫자여야 함
        
        # 패턴: (책이름)\s*(\d+):(\d+)(?:\s*-\s*(?:(\S+?)\s*)?(\d+):(\d+))?
        # Group 1: 시작 책 이름 (예: 요한복음)
        # Group 2: 시작 장 (예: 3)
        # Group 3: 시작 절 (예: 16)
        # Group 4: 끝 책 이름 (선택적, 예: 요한복음)
        # Group 5: 끝 장 (예: 18)
        # Group 6: 끝 절 (예: 18)

        # 더 간단한 패턴: 책이름 숫자:숫자 (- 숫자:숫자)
        # `core/tasks.py`의 파싱 로직과 유사하게
        pattern = re.compile(r'^\s*(.+?)\s*(\d+):(\d+)\s*(?:-\s*(?:(.+?)\s*)?(\d+):(\d+))?\s*$')
        
        match = pattern.match(scripture)
        if not match:
            raise forms.ValidationError("올바른 성경 본문 범위 형식이 아닙니다. '책이름 장:절 - 장:절' 또는 '책이름 장:절' 형식을 따르세요.")
        
        # 추가적인 논리적 유효성 검사 (시작 절/장 > 끝 절/장 등)
        try:
            start_book = match.group(1).strip()
            start_ch = int(match.group(2))
            start_verse = int(match.group(3))
            
            end_book = match.group(4) # None일 수 있음
            end_ch = int(match.group(5)) if match.group(5) else start_ch # 끝 장 없으면 시작 장과 동일
            end_verse = int(match.group(6)) if match.group(6) else start_verse # 끝 절 없으면 시작 절과 동일
            
            # 끝 책 이름이 명시되었다면 시작 책 이름과 같아야 함 (다르면 오류)
            if end_book and end_book.strip() != start_book:
                raise forms.ValidationError("시작과 끝 성경책 이름이 다릅니다. 동일한 성경책 내에서만 범위를 지정할 수 있습니다.")

            # 시작 절/장이 끝 절/장보다 큰 경우 오류
            if start_ch > end_ch:
                raise forms.ValidationError("시작 장이 끝 장보다 큽니다.")
            if start_ch == end_ch and start_verse > end_verse:
                raise forms.ValidationError("시작 절이 끝 절보다 큽니다.")

        except (ValueError, TypeError): # int 변환 실패 등
            raise forms.ValidationError("장과 절은 숫자로 입력해야 합니다.")
        
        return scripture # 유효하면 원본 스크립처 반환


class SongInfoForm(forms.ModelForm):
    """
    찬양 정보 입력을 위한 폼.
    찬양팀이 사용합니다.
    """
    class Meta:
        model = SongInfo
        # worship_info는 상위 폼(WorshipInfoForm)에서 자동으로 연결되므로 여기서는 제외합니다.
        # lyrics와 lyrics_pages는 크롤링/LLM으로 자동 채워지므로 제외합니다.
        fields = ['order', 'title', 'source_url', 'is_ending_song']
        labels = {
            'order': '찬양 순서',
            'title': '찬양 제목',
            'source_url': '가사 URL(현재 Bugs 사이트만 지원)',
            'is_ending_song': '결단 찬양 여부',
        }
        widgets = {
            'order': forms.HiddenInput(), # 순서는 자동으로 관리되므로 숨김 필드로 처리
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '예: 은혜 아니면'
            }),
            'source_url': forms.URLInput(attrs={ # 위젯도 'source_url'로 변경
                'class': 'form-input',
                'placeholder': '예: https://music.bugs.co.kr/track/7004582' # 플레이스홀더 변경
            }),
            'is_ending_song': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

# SongInfoFormSet을 위한 BaseFormSet 정의
class BaseSongInfoFormSet(BaseInlineFormSet):
    def clean(self):
        """
        폼셋 전체의 유효성을 검사합니다.
        특히 한 예배에 결단 찬양이 하나만 있는지 검사합니다.
        """
        super().clean()

        ending_songs_count = 0
        for form in self.forms:
            # 삭제되지 않은(cleaned_data가 있고 DELETE 체크박스가 체크되지 않은) 폼만 검사
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                if form.cleaned_data.get('is_ending_song'):
                    ending_songs_count += 1
        
        if ending_songs_count > 1:
            # 폼셋 전체에 유효성 오류 추가
            raise forms.ValidationError("결단 찬양은 예배당 하나만 지정할 수 있습니다.")
        elif ending_songs_count == 0 and self.forms: # 모든 폼이 존재하는데 결단찬양이 하나도 없으면 경고 (선택적)
             # messages.warning(self.request, "Warning: 최소 하나 이상의 결단 찬양을 지정해주세요.") # 뷰에서 메시지 처리
             pass # 모델 제약에서 잡아주므로 여기서는 1개 초과만 집중

# WorshipInfo와 SongInfo를 한 페이지에서 함께 관리하기 위한 폼셋
# 예배 정보에 여러 찬양 정보가 연결될 수 있으므로 inlineformset_factory를 사용합니다.
SongInfoFormSet = inlineformset_factory(
    WorshipInfo, # 부모 모델
    SongInfo,    # 자식 모델
    form=SongInfoForm,
    fields=['order', 'title', 'source_url', 'is_ending_song'],
    extra=1,     # 기본으로 보여줄 빈 폼의 개수
    can_delete=True, # 기존 객체 삭제 허용
    can_order=True,
    formset=BaseSongInfoFormSet, # 커스텀 BaseFormSet 사용
)