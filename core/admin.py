from django.contrib import admin
from .models import WorshipInfo, SongInfo, PptRequest, PptTemplate

# 각 모델을 Django 관리자 페이지에 등록합니다.
# 이렇게 등록하면 웹 인터페이스를 통해 데이터 생성, 조회, 수정, 삭제가 가능해집니다.

@admin.register(WorshipInfo)
class WorshipInfoAdmin(admin.ModelAdmin):
    list_display = ('worship_date', 'worship_type', 'speaker', 'sermon_title', 'created_by', 'created_at')
    list_filter = ('worship_type', 'is_llm_processed')
    search_fields = ('sermon_title', 'speaker', 'announcements')
    date_hierarchy = 'worship_date' # 날짜 필드로 계층적 탐색

@admin.register(SongInfo)
class SongInfoAdmin(admin.ModelAdmin):
    list_display = ('worship_info', 'order', 'title', 'youtube_url', 'created_by')
    list_filter = ('worship_info__worship_type',)
    search_fields = ('title', 'lyrics')
    raw_id_fields = ('worship_info', 'created_by') # 외래키 필드를 ID로 입력 가능하게 하여 효율성 높임

@admin.register(PptRequest)
class PptRequestAdmin(admin.ModelAdmin):
    list_display = ('worship_info', 'status', 'requested_by', 'created_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('worship_info__sermon_title', 'progress_message')
    raw_id_fields = ('worship_info', 'requested_by')
    date_hierarchy = 'created_at'

@admin.register(PptTemplate)
class PptTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'template_file', 'created_by', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    raw_id_fields = ('created_by',)