# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin # 권한 데코레이터/믹스인을 위한 기본 Mixin
from django.contrib import messages # 메시지 프레임워크 임포트
from datetime import date, timedelta
import json # JSONField 처리를 위해 임포트

from .models import WorshipInfo, SongInfo, PptRequest
from .forms import WorshipInfoForm, SongInfoFormSet # 새로 생성한 폼 임포트

from django.http import HttpResponse
from django.core.files.storage import default_storage

from django.utils.decorators import method_decorator

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

# 예배준비팀 권한 체크
def worship_prep_team_required(function):
    def wrapper(request, *args, **kwargs):
        if not is_member_of_group(request.user, '예배준비팀'):
            messages.error(request, "예배준비팀만 이 페이지에 접근할 수 있습니다.")
            return redirect('home')
        return function(request, *args, **kwargs)
    return wrapper

@login_required
@worship_prep_team_required
def worship_info_input_view(request):
    """
    예배 정보를 입력하거나 수정하는 페이지.
    예배준비팀만 접근 가능.
    """
    # 이번 주 주일 날짜 계산 (home 뷰와 동일)
    today = date.today()
    days_until_sunday = (6 - today.weekday() + 7) % 7
    if today.weekday() == 6:
        upcoming_sunday = today + timedelta(days=7)
    else:
        upcoming_sunday = today + timedelta(days=days_until_sunday)

    worship_info = None
    initial_data = {'worship_date': upcoming_sunday} # 새 객체 생성 시 초기값

    try:
        worship_info = WorshipInfo.objects.get(worship_date=upcoming_sunday)
        # JSONField 데이터를 폼에서 편집하기 위해 Python 객체(리스트/딕셔너리)를 JSON 문자열로 변환
        if worship_info.worship_announcements:
            initial_data['worship_announcements'] = json.dumps(worship_info.worship_announcements, indent=2, ensure_ascii=False)
        else:
            initial_data['worship_announcements'] = '[]' # 빈 JSON 리스트 기본값
        
    except WorshipInfo.DoesNotExist:
        pass # 객체가 없으면 새로 생성

    if request.method == 'POST':
        form = WorshipInfoForm(request.POST, instance=worship_info, initial=initial_data)
        if form.is_valid():
            worship_info_obj = form.save(commit=False)
            worship_info_obj.created_by = request.user # 생성자 설정
            
            # JSON 필드 처리: 폼에서 문자열로 받은 JSON을 Python 객체로 변환하여 저장
            if worship_info_obj.worship_announcements:
                try:
                    worship_info_obj.worship_announcements = json.loads(request.POST.get('worship_announcements', '[]'))
                except json.JSONDecodeError:
                    messages.error(request, "광고 목록 필드에 유효하지 않은 JSON 형식이 입력되었습니다.")
                    return render(request, 'core/worship_info_form.html', {'form': form})
            else:
                worship_info_obj.worship_announcements = [] # 비어있으면 빈 리스트 저장

            worship_info_obj.save()
            messages.success(request, f"{upcoming_sunday} 예배 정보가 성공적으로 저장되었습니다.")

            # PptRequest가 아직 없으면 생성 (상태는 'no_song_info' 또는 'pending'으로 초기화)
            ppt_request_obj, created = PptRequest.objects.get_or_create(
                worship_info=worship_info_obj,
                defaults={'requested_by': request.user, 'status': 'pending'} # 처음 생성 시 상태
            )
            if not created:
                # 이미 PptRequest가 존재하면 상태를 'no_song_info'가 아닌 'pending'으로 업데이트
                if ppt_request_obj.status == 'no_worship_info':
                     ppt_request_obj.status = 'pending'
                     ppt_request_obj.progress_message = "예배 정보가 입력되었습니다. 찬양 정보 입력을 기다립니다."
                     ppt_request_obj.save()

            return redirect('home')
        else:
            messages.error(request, "예배 정보 저장에 실패했습니다. 입력 양식을 확인해주세요.")
    else:
        form = WorshipInfoForm(instance=worship_info, initial=initial_data)

    context = {
        'form': form,
        'upcoming_sunday': upcoming_sunday,
    }
    return render(request, 'core/worship_info_form.html', context)


# 찬양팀 권한 체크
def praise_team_required(function):
    def wrapper(request, *args, **kwargs):
        if not is_member_of_group(request.user, '찬양팀'):
            messages.error(request, "찬양팀만 이 페이지에 접근할 수 있습니다.")
            return redirect('home')
        return function(request, *args, **kwargs)
    return wrapper

@login_required
@praise_team_required
def song_info_input_view(request):
    """
    찬양 정보를 입력하거나 수정하는 페이지.
    찬양팀만 접근 가능.
    """
    today = date.today()
    days_until_sunday = (6 - today.weekday() + 7) % 7
    if today.weekday() == 6:
        upcoming_sunday = today + timedelta(days=7)
    else:
        upcoming_sunday = today + timedelta(days=days_until_sunday)

    worship_info = None
    try:
        worship_info = WorshipInfo.objects.get(worship_date=upcoming_sunday)
    except WorshipInfo.DoesNotExist:
        messages.error(request, "해당 주일 예배 정보가 먼저 입력되어야 찬양 정보를 입력할 수 있습니다.")
        return redirect('home')

    if request.method == 'POST':
        formset = SongInfoFormSet(request.POST, request.FILES, instance=worship_info)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk:
                    instance.created_by = request.user
                instance.save()
            
            # formset.save_m2m() # SongInfo에는 M2M 관계가 없으므로 필요 없음
            
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, f"{upcoming_sunday} 찬양 정보가 성공적으로 저장되었습니다.")

            ppt_request_obj, created = PptRequest.objects.get_or_create(
                worship_info=worship_info,
                defaults={'requested_by': request.user, 'status': 'pending'}
            )
            if not created:
                if ppt_request_obj.status == 'no_song_info':
                    ppt_request_obj.status = 'pending'
                    ppt_request_obj.progress_message = "찬양 정보가 입력되었습니다. PPT 제작을 시작할 수 있습니다."
                    ppt_request_obj.save()

            return redirect('home')
        else:
            messages.error(request, "찬양 정보 저장에 실패했습니다. 입력 양식을 확인해주세요.")
    else:
        formset = SongInfoFormSet(instance=worship_info)

    context = {
        'formset': formset,
        'worship_info': worship_info,
    }
    return render(request, 'core/song_info_form.html', context)


# --- 임시 뷰 함수들 (향후 실제 뷰로 대체되거나 로직 추가 예정) ---
@login_required
def ppt_creation_start_view(request):
    """미디어팀만 접근 가능"""
    if not is_member_of_group(request.user, '미디어팀'):
        messages.error(request, "미디어팀만 이 페이지에 접근할 수 있습니다.")
        return redirect('home')
    return render(request, 'core/ppt_creation_start.html') # 새로운 템플릿 생성 예정

@login_required
def ppt_download_view(request, ppt_request_id):
    """
    PPT 다운로드 뷰.
    이 뷰는 메인 페이지에서 'PPT 다운로드' 버튼 클릭 시 호출됩니다.
    실제 구현 시 FileResponse 등을 사용하여 파일을 다운로드하도록 처리합니다.
    """
    ppt_request = get_object_or_404(PptRequest, id=ppt_request_id)
    
    # 보안: 권한이 있는 사용자만 다운로드 가능하도록 추후 로직 추가 필요
    # 예: if not is_member_of_group(request.user, '미디어팀'): ...
    
    if ppt_request.generated_ppt_file:
        # 실제 파일 다운로드 로직 (간단한 예시, 실제 배포 시에는 더 견고하게)
        file_path = ppt_request.generated_ppt_file.path
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
                response['Content-Disposition'] = f'attachment; filename="{ppt_request.generated_ppt_file.name}"'
                return response
        else:
            messages.error(request, "생성된 PPT 파일이 존재하지 않습니다.")
    else:
        messages.error(request, "다운로드할 PPT 파일이 없습니다.")
    
    return redirect('home') # 파일 없거나 오류 시 메인 페이지로 리다이렉트