# core/forms.py

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
            'ads_manager', 'main_prayer_topic', 'worship_announcements', 'notes',
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
            'main_prayer_topic': '예배 기도 제목',
            'worship_announcements': '광고 목록 (JSON)', # JSONField는 텍스트 입력으로 받습니다.
            'notes': '추가 비고',
        }
        # 위젯을 사용하여 폼 필드의 HTML 표현을 커스터마이징할 수 있습니다.
        widgets = {
            'worship_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}), # 날짜 선택기를 제공
            'worship_type': forms.Select(attrs={'class': 'form-select'}),
            'speaker': forms.TextInput(attrs={'class': 'form-input'}),
            'sermon_title': forms.TextInput(attrs={'class': 'form-input'}),
            'sermon_scripture': forms.TextInput(attrs={'class': 'form-input'}),
            'prayer_minister': forms.TextInput(attrs={'class': 'form-input'}),
            'offering_minister': forms.TextInput(attrs={'class': 'form-input'}),
            'ads_manager': forms.TextInput(attrs={'class': 'form-input'}),
            'main_prayer_topic': forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea'}),
            'worship_announcements': forms.Textarea(attrs={'rows': 6, 'class': 'form-textarea', 'placeholder': 'JSON 형식으로 입력하세요: [{"title": "광고1", "contents": "내용1"}, ...]'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
        }

    def clean_worship_announcements(self):
        """worship_announcements 필드의 JSON 유효성을 검사합니다."""
        data = self.cleaned_data.get('worship_announcements')
        if data:
            try:
                # JSON 문자열을 Python 객체로 변환 시도
                json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("유효한 JSON 형식으로 광고 목록을 입력해주세요.")
        return data


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