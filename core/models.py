from django.db import models
from django.contrib.auth import get_user_model # User 모델을 가져오는 표준 방법
from django.utils import timezone # 날짜 및 시간 관리를 위함

# Django의 기본 User 모델을 가져옵니다.
# 나중에 커스텀 User 모델로 변경하더라도 이 함수를 사용하면 유연합니다.
User = get_user_model()

class TimestampedModel(models.Model):
    """
    생성 및 수정 시간을 자동으로 기록하는 추상 기본 모델.
    모든 모델에 공통적으로 적용될 필드를 정의합니다.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        abstract = True # 이 모델은 데이터베이스 테이블을 생성하지 않고, 다른 모델에 상속됩니다.
        # 추상 모델은 migrate되지 않으므로, 이 모델은 실제 DB 테이블을 생성하지 않습니다.
        # 따라서 created_at, updated_at 필드는 상속받는 자식 모델에 직접 생성됩니다.

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
    sermon_scripture = models.CharField(max_length=255, blank=True, verbose_name="설교 본문")
    announcements = models.TextField(blank=True, verbose_name="광고 내용")
    prayer_topic = models.TextField(blank=True, verbose_name="기도 제목")
    notes = models.TextField(blank=True, verbose_name="추가 비고")
    # 사용자가 Form으로 입력한 경우 LLM 처리가 필요 없으므로, 이를 구분하는 플래그
    is_llm_processed = models.BooleanField(default=False, verbose_name="LLM 처리 여부")

    # 누가 이 예배 정보를 생성했는지 기록 (User 모델과 외래키 관계)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # 사용자가 삭제되어도 예배 정보는 남김
        null=True, # 데이터베이스에 null을 허용
        blank=True, # 폼에서 빈 값을 허용
        related_name='worship_infos',
        verbose_name="등록자"
    )

    class Meta:
        verbose_name = "예배 정보" # Admin 페이지에 표시될 단수 이름
        verbose_name_plural = "예배 정보" # Admin 페이지에 표시될 복수 이름
        ordering = ['-worship_date', 'worship_type'] # 최신 날짜순, 종류순 정렬

    def __str__(self):
        # Admin 페이지 등에서 객체를 문자열로 표현할 때 사용
        return f"{self.worship_date} - {self.get_worship_type_display()}"


class SongInfo(TimestampedModel):
    """
    찬양 정보를 저장하는 모델.
    특정 예배 정보와 연결됩니다.
    """
    worship_info = models.ForeignKey(
        WorshipInfo,
        on_delete=models.CASCADE, # 예배 정보 삭제 시 찬양 정보도 함께 삭제
        related_name='song_infos',
        verbose_name="연결된 예배 정보"
    )
    order = models.PositiveIntegerField(verbose_name="찬양 순서")
    title = models.CharField(max_length=200, verbose_name="찬양 제목")
    youtube_url = models.URLField(max_length=500, blank=True, verbose_name="찬양 영상 URL")
    
    # 크롤링된 전체 가사 (LLM 처리 전 원본)
    lyrics = models.TextField(blank=True, verbose_name="전체 찬양 가사")
    
    # LLM이 페이지별로 나눈 가사 리스트 (JSONField로 저장)
    # 리스트 형태: ["1페이지 가사", "2페이지 가사", ...]
    lyrics_pages = models.JSONField(default=list, blank=True, verbose_name="페이지별 가사")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='song_infos',
        verbose_name="등록자"
    )

    class Meta:
        verbose_name = "찬양 정보"
        verbose_name_plural = "찬양 정보"
        # 한 예배에 같은 순서의 찬양은 중복 불가
        unique_together = ('worship_info', 'order')
        ordering = ['worship_info__worship_date', 'order'] # 예배 날짜, 순서별 정렬

    def __str__(self):
        return f"[{self.worship_info.worship_date}] {self.order}. {self.title}"


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
        ('no_song_info', '찬양 정보 없음'), # 찬양팀이 정보 미입력
        ('no_worship_info', '예배 정보 없음'), # 예배준비팀이 정보 미입력
    )

    worship_info = models.OneToOneField(
        WorshipInfo,
        on_delete=models.CASCADE, # 예배 정보 삭제 시 요청도 함께 삭제
        related_name='ppt_request', # WorshipInfo에서 PptRequest에 접근할 때 사용
        verbose_name="연결된 예배 정보"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="제작 상태"
    )
    # 생성된 PPT 파일 (media/ppts/ 디렉토리에 저장)
    # Django FileField는 DB에 파일 경로(VARCHAR)를 저장하고 실제 파일은 파일 시스템에 저장합니다.
    generated_ppt_file = models.FileField(
        upload_to='ppts/', # MEDIA_ROOT/ppts/ 에 저장됩니다. (settings.py에 MEDIA_ROOT 설정 필요)
        blank=True,
        null=True,
        verbose_name="생성된 PPT 파일"
    )
    # Celery 작업의 ID (작업 상태 추적용)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="Celery 작업 ID")
    # 사용자에게 보여줄 진행 상황 메시지
    progress_message = models.CharField(max_length=255, blank=True, verbose_name="진행 상황 메시지")

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ppt_requests',
        verbose_name="요청자"
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료 일시")

    class Meta:
        verbose_name = "PPT 제작 요청"
        verbose_name_plural = "PPT 제작 요청"
        ordering = ['-created_at'] # 최신 요청순 정렬 (created_at으로 변경)

    def __str__(self):
        return f"PPT Request for {self.worship_info.worship_date} - Status: {self.get_status_display()}"


class PptTemplate(TimestampedModel):
    """
    PPT 템플릿 파일을 관리하는 모델.
    미디어팀이 사용할 PPTX 템플릿 파일을 업로드하고 관리합니다.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="템플릿 이름")
    template_file = models.FileField(
        upload_to='ppt_templates/', # MEDIA_ROOT/ppt_templates/ 에 저장됩니다.
        verbose_name="템플릿 파일 (.pptx)"
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    description = models.TextField(blank=True, verbose_name="템플릿 설명")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ppt_templates',
        verbose_name="등록자"
    )

    class Meta:
        verbose_name = "PPT 템플릿"
        verbose_name_plural = "PPT 템플릿"
        ordering = ['-created_at']

    def __str__(self):
        return self.name