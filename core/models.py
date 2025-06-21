# core/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class TimestampedModel(models.Model):
    """
    생성 및 수정 시간을 자동으로 기록하는 추상 기본 모델.
    모든 모델에 공통적으로 적용될 필드를 정의합니다.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        abstract = True


class WorshipInfo(TimestampedModel):
    """
    예배 정보를 저장하는 모델.
    주로 예배의 기본적인 정보들을 기록합니다.
    """
    WORSHIP_TYPES = (
        ('sunday_am', '주일 오전 예배'),
        ('sunday_pm', '주일 오후 예배'),
        ('wednesday', '수요 예배'),
        ('friday', '금요 철야 예배'),
        ('dawn', '새벽 예배'),
        ('other', '기타 예배'),
    )

    worship_date = models.DateField(unique=True, verbose_name="예배 날짜")
    worship_type = models.CharField(
        max_length=20,
        choices=WORSHIP_TYPES,
        default='sunday_am',
        verbose_name="예배 종류"
    )
    speaker = models.CharField(max_length=100, blank=True, verbose_name="설교자")
    sermon_title = models.CharField(max_length=200, blank=True, verbose_name="설교 제목")
    sermon_scripture = models.CharField(max_length=255, blank=True, verbose_name="설교 본문 범위") # 이름 변경

    prayer_minister = models.CharField(max_length=100, blank=True, verbose_name="기도자")
    offering_minister = models.CharField(max_length=100, blank=True, verbose_name="봉헌자")
    ads_manager = models.CharField(max_length=100, blank=True, verbose_name="광고 담당자") # 광고 책임자명
    benediction_minister = models.CharField(max_length=100, blank=True, verbose_name="축도자") # 축도자명
    worship_announcements = models.JSONField(default=list, blank=True, verbose_name="광고 목록") # 구조화된 광고 내용
    main_prayer_topic = models.TextField(blank=True, verbose_name="예배 기도 제목")

    notes = models.TextField(blank=True, verbose_name="추가 비고")
    is_llm_processed = models.BooleanField(default=False, verbose_name="LLM 처리 여부")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='worship_infos_created', # related_name 충돌 방지 위해 변경
        verbose_name="등록자"
    )

    class Meta:
        verbose_name = "예배 정보"
        verbose_name_plural = "예배 정보"
        ordering = ['-worship_date', 'worship_type']

    def __str__(self):
        return f"{self.worship_date} - {self.get_worship_type_display()}"


class SongInfo(TimestampedModel):
    """
    찬양 정보를 저장하는 모델.
    특정 예배 정보와 연결됩니다.
    """
    worship_info = models.ForeignKey(
        WorshipInfo,
        on_delete=models.CASCADE,
        related_name='song_infos',
        verbose_name="연결된 예배 정보"
    )
    order = models.PositiveIntegerField(verbose_name="찬양 순서")
    title = models.CharField(max_length=200, verbose_name="찬양 제목")
    youtube_url = models.URLField(max_length=500, blank=True, verbose_name="찬양 영상 URL")

    lyrics = models.TextField(blank=True, verbose_name="전체 찬양 가사")
    lyrics_pages = models.JSONField(default=list, blank=True, verbose_name="페이지별 가사")

    is_ending_song = models.BooleanField(default=False, verbose_name="결단 찬양 여부")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='song_infos_created', # related_name 충돌 방지 위해 변경
        verbose_name="등록자"
    )

    class Meta:
        verbose_name = "찬양 정보"
        verbose_name_plural = "찬양 정보"
        unique_together = ('worship_info', 'order', 'is_ending_song') # 결단찬양은 순서 중복 가능성 고려하여 추가
        ordering = ['worship_info__worship_date', 'order', 'is_ending_song']

    def __str__(self):
        song_type = "결단 찬양" if self.is_ending_song else "찬양"
        return f"[{self.worship_info.worship_date}] {song_type} ({self.order}). {self.title}"


class PptRequest(TimestampedModel):
    """
    PPT 제작 요청 및 상태를 저장하는 모델.
    각 예배 정보와 연결되며, PPT 제작의 진행 상황을 추적합니다.
    """
    STATUS_CHOICES = (
        ('pending', '대기 중'),
        ('processing', '제작 중'),
        ('completed', '제작 완료'),
        ('failed', '제작 실패'),
        ('no_song_info', '찬양 정보 없음'),
        ('no_worship_info', '예배 정보 없음'),
    )

    worship_info = models.OneToOneField(
        WorshipInfo,
        on_delete=models.CASCADE,
        related_name='ppt_request',
        verbose_name="연결된 예배 정보"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="제작 상태"
    )
    generated_ppt_file = models.FileField(
        upload_to='ppts/',
        blank=True,
        null=True,
        verbose_name="생성된 PPT 파일"
    )
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Celery 작업 ID")
    progress_message = models.CharField(max_length=255, blank=True, verbose_name="진행 상황 메시지")

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ppt_requests_created', # related_name 충돌 방지 위해 변경
        verbose_name="요청자"
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료 일시")

    class Meta:
        verbose_name = "PPT 제작 요청"
        verbose_name_plural = "PPT 제작 요청"
        ordering = ['-created_at']

    def __str__(self):
        return f"PPT Request for {self.worship_info.worship_date} - Status: {self.get_status_display()}"


class PptTemplate(TimestampedModel):
    """
    PPT 템플릿 파일을 관리하는 모델.
    미디어팀이 사용할 PPTX 템플릿 파일을 업로드하고 관리합니다.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="템플릿 이름")
    template_file = models.FileField(
        upload_to='ppt_templates/',
        verbose_name="템플릿 파일 (.pptx)"
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    description = models.TextField(blank=True, verbose_name="템플릿 설명")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ppt_templates_created', # related_name 충돌 방지 위해 변경
        verbose_name="등록자"
    )

    class Meta:
        verbose_name = "PPT 템플릿"
        verbose_name_plural = "PPT 템플릿"
        ordering = ['-created_at']

    def __str__(self):
        return self.name