# core/forms.py

import json
from django import forms
from .models import WorshipInfo, SongInfo # 우리가 정의한 모델 임포트
from django.forms import inlineformset_factory # SongInfo를 WorshipInfo와 함께 관리하기 위함

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
            'sermon_scripture': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 출애굽기 3:4-12'}),
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


class SongInfoForm(forms.ModelForm):
    """
    찬양 정보 입력을 위한 폼.
    찬양팀이 사용합니다.
    """
    class Meta:
        model = SongInfo
        # worship_info는 상위 폼(WorshipInfoForm)에서 자동으로 연결되므로 여기서는 제외합니다.
        # lyrics와 lyrics_pages는 크롤링/LLM으로 자동 채워지므로 제외합니다.
        fields = ['order', 'title', 'youtube_url', 'is_ending_song']
        labels = {
            'order': '찬양 순서',
            'title': '찬양 제목',
            'youtube_url': 'YouTube URL',
            'is_ending_song': '결단 찬양 여부',
        }
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-input'}),
            'is_ending_song': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

# WorshipInfo와 SongInfo를 한 페이지에서 함께 관리하기 위한 폼셋
# 예배 정보에 여러 찬양 정보가 연결될 수 있으므로 inlineformset_factory를 사용합니다.
SongInfoFormSet = inlineformset_factory(
    WorshipInfo, # 부모 모델
    SongInfo,    # 자식 모델
    form=SongInfoForm,
    fields=['order', 'title', 'youtube_url', 'is_ending_song'],
    extra=1,     # 기본으로 보여줄 빈 폼의 개수
    can_delete=True, # 기존 객체 삭제 허용
    can_order=False, # 순서 변경 기능 비활성화 (Order 필드로 직접 관리)
)