# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin # 권한 데코레이터/믹스인을 위한 기본 Mixin
from datetime import date, timedelta
from .models import WorshipInfo, SongInfo, PptRequest
from django.http import HttpResponse # 임시 뷰를 위한 임포트

# User 모델을 가져오는 표준 방법 (models.py와 동일하게 유지)
from django.contrib.auth import get_user_model
User = get_user_model()

# 권한 체크를 위한 헬퍼 함수 (재사용성을 위해 별도로 정의)
def is_member_of_group(user, group_name):
    """주어진 사용자가 특정 그룹의 멤버인지 확인합니다."""
    return user.groups.filter(name=group_name).exists()

@login_required # 로그인한 사용자만 접근 가능
def home(request):
    """
    메인 페이지 뷰.
    이번 주 주일 예배 정보와 PPT 제작 현황을 표시하고,
    사용자 역할에 따라 버튼을 조건부로 노출합니다.
    """

    # 1. 이번 주 주일 날짜 계산
    today = date.today()
    # 요일 가져오기 (월요일=0, 일요일=6)
    days_until_sunday = (6 - today.weekday() + 7) % 7
    # 오늘이 일요일이면 다음 주 일요일 (오늘 포함)
    # 오늘이 일요일이 아니면 이번 주 일요일 (가장 가까운 미래의 일요일)
    if today.weekday() == 6: # 오늘이 일요일이면, 다음 주 일요일을 기준으로 합니다.
        upcoming_sunday = today + timedelta(days=7)
    else:
        upcoming_sunday = today + timedelta(days=days_until_sunday)

    # 2. 해당 주일 예배 정보 조회
    worship_info = None
    ppt_request = None
    ppt_status_display = "정보 없음"

    try:
        worship_info = WorshipInfo.objects.get(worship_date=upcoming_sunday)

        # 3. PPT 제작 현황 조회
        try:
            ppt_request = PptRequest.objects.get(worship_info=worship_info)
            ppt_status_display = ppt_request.get_status_display() # 모델에 정의된 get_status_display 사용
        except PptRequest.DoesNotExist:
            # 예배 정보는 있으나 PPT 요청이 없는 경우
            ppt_status_display = "PPT 요청 대기"

        # 찬양 정보가 입력되었는지 확인 (SongInfo가 연결된 WorshipInfo에 존재하는지)
        if not SongInfo.objects.filter(worship_info=worship_info).exists():
            if ppt_request and ppt_request.status not in ['completed', 'failed']: # 이미 완료나 실패는 제외
                 ppt_status_display = "찬양 정보 없음" # 찬양팀에 메시지
            elif not ppt_request:
                 ppt_status_display = "찬양 정보 없음"

    except WorshipInfo.DoesNotExist:
        # 해당 주일 예배 정보 자체가 없는 경우
        ppt_status_display = "예배 정보 없음" # 예배준비팀에 메시지

    # 4. 사용자 역할 정보
    user_is_media_team = is_member_of_group(request.user, '미디어팀')
    user_is_praise_team = is_member_of_group(request.user, '찬양팀')
    user_is_worship_prep_team = is_member_of_group(request.user, '예배준비팀')
    user_is_member = is_member_of_group(request.user, '교인') # 교인도 현황 조회 가능

    context = {
        'username': request.user.username,
        'upcoming_sunday': upcoming_sunday,
        'worship_info': worship_info,
        'ppt_request': ppt_request,
        'ppt_status_display': ppt_status_display,

        # 역할별 플래그
        'user_is_media_team': user_is_media_team,
        'user_is_praise_team': user_is_praise_team,
        'user_is_worship_prep_team': user_is_worship_prep_team,
        'user_is_member': user_is_member, # 교인 역할 추가

        # 버튼 노출 조건
        'show_ppt_creation_start_button': user_is_media_team and ppt_request and ppt_request.status != 'completed',
        'show_worship_info_input_button': user_is_worship_prep_team and not worship_info,
        'show_song_info_input_button': user_is_praise_team and worship_info and not SongInfo.objects.filter(worship_info=worship_info).exists(),
    }

    return render(request, 'core/home.html', context)

# --- 임시 뷰 함수들 (향후 실제 뷰로 대체될 예정) ---
@login_required
def worship_info_input_view(request):
    return HttpResponse("<h2>예배 정보 입력 페이지 (임시)</h2><p>여기는 예배준비팀이 예배 정보를 입력하는 페이지입니다.</p><a href='/'>메인으로</a>")

@login_required
def song_info_input_view(request):
    return HttpResponse("<h2>찬양 정보 입력 페이지 (임시)</h2><p>여기는 찬양팀이 찬양 정보를 입력하는 페이지입니다.</p><a href='/'>메인으로</a>")

@login_required
def ppt_creation_start_view(request):
    return HttpResponse("<h2>PPT 제작 시작 페이지 (임시)</h2><p>여기는 미디어팀이 PPT 제작을 시작하는 페이지입니다.</p><a href='/'>메인으로</a>")

@login_required
def ppt_download_view(request, ppt_request_id):
    # 실제 구현 시에는 FileResponse 등을 사용하여 파일을 다운로드하도록 처리합니다.
    return HttpResponse(f"<h2>PPT 다운로드 페이지 (임시)</h2><p>PPT 요청 ID: {ppt_request_id} 파일을 다운로드합니다.</p><a href='/'>메인으로</a>")