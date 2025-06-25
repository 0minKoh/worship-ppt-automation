# core/views.py

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin # 권한 데코레이터/믹스인을 위한 기본 Mixin
from django.contrib import messages # 메시지 프레임워크 임포트
from datetime import date, timedelta
import json # JSONField 처리를 위해 임포트

from .models import WorshipInfo, SongInfo, PptRequest
from .forms import WorshipInfoForm, SongInfoFormSet

from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.db import transaction

from django.utils.decorators import method_decorator

# Celery 태스크 임포트
from core.tasks import generate_ppt_task


# User 모델을 가져오는 표준 방법 (models.py와 동일하게 유지)
from django.contrib.auth import get_user_model
User = get_user_model()

# 권한 체크를 위한 헬퍼 함수 (재사용성을 위해 별도로 정의)
def is_member_of_group(user, group_name):
    """주어진 사용자가 특정 그룹의 멤버인지 확인합니다."""
    return user.groups.filter(name=group_name).exists()

# 미디어팀 / 슈퍼유저 권한 체크
def is_media_team_or_superuser(user) -> bool:
    """
    사용자가 미디어팀의 멤버이거나 슈퍼유저인지 확인합니다.
    """
    return user.is_superuser or is_member_of_group(user, '미디어팀')

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
        'show_worship_info_input_button': (user_is_worship_prep_team or user_is_media_team) and not worship_info,
        'show_song_info_input_button': (user_is_praise_team or user_is_media_team) and worship_info and not SongInfo.objects.filter(worship_info=worship_info).exists(),
    }

    return render(request, 'core/home.html', context)

# 예배준비팀 권한 체크
def worship_prep_team_required(function):
    def wrapper(request, *args, **kwargs):
        if is_media_team_or_superuser(request.user): # 미디어팀이나 슈퍼유저는 예배준비팀 권한을 우회
            return function(request, *args, **kwargs)
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
            initial_data['worship_announcements'] = worship_info.worship_announcements
        else:
            initial_data['worship_announcements'] = '[]' # 빈 JSON 리스트 기본값
        
    except WorshipInfo.DoesNotExist:
        pass # 객체가 없으면 새로 생성

    if request.method == 'POST':
        form = WorshipInfoForm(request.POST, instance=worship_info, initial=initial_data)
        if form.is_valid():
            worship_info_obj = form.save(commit=False)
            worship_info_obj.created_by = request.user # 생성자 설정

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
        if is_media_team_or_superuser(request.user): # 미디어팀이나 슈퍼유저는 예배준비팀 권한을 우회
            return function(request, *args, **kwargs)
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
            try:
                with transaction.atomic(): # <--- 트랜잭션 시작: 모든 DB 작업은 이 블록 안에서 원자적으로 처리
                    # 새로운 SongInfo 객체 생성 및 변경된 객체 저장
                    # formset.save()는 commit=False가 아닐 경우, 내부적으로 transaction.atomic()을 사용하며
                    # 모든 생성, 변경, 삭제 작업을 한 번에 처리하고 created_by를 반환하지 않습니다.
                    # 따라서 created_by를 수동으로 설정하려면 commit=False를 사용하고 수동으로 저장해야 합니다.

                    # created_by를 수동으로 할당하기 위해 commit=False로 인스턴스를 가져온 후,
                    # 루프 내에서 created_by를 할당하고 개별적으로 save()를 호출합니다.
                    # 이 방식은 폼셋의 save()가 반환하는 new_objects, changed_objects를 사용합니다.
                    instances_to_save = formset.save(commit=False)
                    for instance in instances_to_save:
                        if not instance.pk: # 새로 생성되는 객체에 대해서만 created_by 할당
                            instance.created_by = request.user
                        instance.save() # 개별 인스턴스를 DB에 저장

                    # 삭제 대상으로 표시된 기존 객체 삭제
                    for obj in formset.deleted_objects:
                        obj.delete()

                messages.success(request, f"{upcoming_sunday} 찬양 정보가 성공적으로 저장되었습니다.")

                # PPT 요청 상태 업데이트 (성공적으로 저장된 후에만)
                ppt_request_obj, created = PptRequest.objects.get_or_create(
                    worship_info=worship_info,
                    defaults={'requested_by': request.user, 'status': 'pending', 'progress_message': '찬양 정보 입력 완료. PPT 제작 대기 중'}
                )
                if not created:
                    if ppt_request_obj.status == 'no_song_info' or ppt_request_obj.status == 'failed':
                        ppt_request_obj.status = 'pending'
                        ppt_request_obj.progress_message = "찬양 정보가 업데이트되었습니다. PPT 제작을 시작할 수 있습니다."
                        ppt_request_obj.save()

                return redirect('home')

            except Exception as e: # <--- 트랜잭션 내에서 발생한 IntegrityError 등의 예외를 여기서 잡음
                # messages.error는 트랜잭션이 롤백된 후에도 작동합니다.
                messages.error(request, f"찬양 정보 저장 중 오류가 발생했습니다: {e}. 입력 양식을 확인해주세요.")
                # 에러 발생 시 formset에 에러가 추가될 것이고, 템플릿에서 렌더링될 것입니다.
        else:
            messages.error(request, "찬양 정보 저장에 실패했습니다. 입력 양식을 확인해주세요.")
    else:
        formset = SongInfoFormSet(instance=worship_info)

    context = {
        'formset': formset,
        'worship_info': worship_info,
    }
    return render(request, 'core/song_info_form.html', context)


@login_required
def ppt_creation_start_view(request):
    """
    PPT 제작을 시작하는 페이지. 미디어팀만 접근 가능.
    GET 요청 시 확인 페이지를 렌더링하고, POST 요청 시 Celery 태스크를 트리거합니다.
    """
    if not is_member_of_group(request.user, '미디어팀'):
        messages.error(request, "미디어팀만 이 페이지에 접근할 수 있습니다.")
        return redirect('home')
    
    # 1. 이번 주 주일 날짜 계산
    today = date.today()
    days_until_sunday = (6 - today.weekday() + 7) % 7
    if today.weekday() == 6: # 오늘이 일요일이면 다음 주 일요일
        upcoming_sunday = today + timedelta(days=7)
    else: # 오늘이 일요일이 아니면 이번 주 일요일
        upcoming_sunday = today + timedelta(days=days_until_sunday)

    # 2. 해당 주일 예배 정보 조회 (없으면 오류)
    worship_info = None
    try:
        worship_info = WorshipInfo.objects.get(worship_date=upcoming_sunday)
    except WorshipInfo.DoesNotExist:
        messages.error(request, f"{upcoming_sunday} 주일 예배 정보가 존재하지 않아 PPT를 제작할 수 없습니다.")
        return redirect('home') # 예배 정보 없으면 메인으로 리다이렉트

    # 3. 찬양 정보 필수 확인 (일반 찬양 및 결단 찬양)
    has_normal_songs = SongInfo.objects.filter(worship_info=worship_info, is_ending_song=False).exists()
    has_ending_song = SongInfo.objects.filter(worship_info=worship_info, is_ending_song=True).exists()

    if not has_normal_songs:
        messages.error(request, f"{upcoming_sunday} 일반 찬양 정보가 입력되지 않아 PPT를 제작할 수 없습니다.")
        return redirect('home')
    if not has_ending_song:
        messages.error(request, f"{upcoming_sunday} 결단 찬양 정보가 입력되지 않아 PPT를 제작할 수 없습니다.")
        return redirect('home')

    # 4. PptRequest 객체 가져오거나 생성
    # 이 부분에서 defaults를 설정할 때, 요청자가 누구인지 명확히 전달합니다.
    # PptRequest의 상태는 'pending' 또는 'failed' 등 재요청 가능한 상태여야 합니다.
    ppt_request, created = PptRequest.objects.get_or_create(
        worship_info=worship_info,
        defaults={'requested_by': request.user, 'status': 'pending', 'progress_message': 'PPT 제작 대기 중'}
    )
    # 이미 존재하는데 상태가 'processing' 또는 'completed'이면 중복 요청 방지
    if not created and ppt_request.status in ['processing', 'completed']:
        messages.warning(request, "이미 PPT 제작이 진행 중이거나 완료되었습니다.")
        return redirect('home')
    
    # 이전 요청이 실패했거나, 정보 누락으로 대기 중이었다면 상태를 'pending'으로 업데이트
    if not created and ppt_request.status in ['failed', 'no_song_info', 'no_worship_info']:
        ppt_request.status = 'pending'
        ppt_request.progress_message = "PPT 제작을 다시 요청할 수 있습니다."
        ppt_request.save()


    if request.method == 'POST':
        # Celery 태스크 실행
        # 태스크에 PptRequest의 ID를 전달하여 태스크 내에서 PptRequest를 업데이트하도록 합니다.
        task_result = generate_ppt_task.delay(worship_info.id) # worship_info_id를 태스크에 전달

        # PptRequest에 Celery 태스크 ID 저장 및 상태 업데이트
        ppt_request.celery_task_id = task_result.id
        ppt_request.status = 'processing'
        ppt_request.progress_message = "PPT 제작 요청을 처리 중입니다..."
        ppt_request.requested_by = request.user # 요청자를 명확히
        ppt_request.save()
        
        messages.success(request, "PPT 제작이 요청되었습니다. 진행 상황을 메인 페이지에서 확인해주세요.")
        return redirect('home')
    
    context = {
        'worship_info': worship_info,
        'ppt_request': ppt_request,
        'upcoming_sunday': upcoming_sunday,
    }
    return render(request, 'core/ppt_creation_start.html', context)

@login_required
def ppt_download_view(request, ppt_request_id):
    """
    PPT 다운로드 뷰.
    이 뷰는 메인 페이지에서 'PPT 다운로드' 버튼 클릭 시 호출됩니다.
    실제 구현 시 FileResponse 등을 사용하여 파일을 다운로드하도록 처리합니다.
    """
    ppt_request = get_object_or_404(PptRequest, id=ppt_request_id)
    
    # 다운로드 권한 체크 (추후 더 상세히 구현 가능)
    # 모든 로그인 사용자에게 허용 (임시)
    
    if not ppt_request.generated_ppt_file or ppt_request.status != 'completed':
        messages.error(request, "다운로드할 PPT 파일이 없거나, 아직 제작 완료되지 않았습니다.")
        return redirect('home')

    file_path = ppt_request.generated_ppt_file.path
    if default_storage.exists(file_path):
        from django.http import FileResponse
        try:
            response = FileResponse(default_storage.open(file_path, 'rb'), 
                                    content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
            # 파일명을 UTF-8로 인코딩하여 한글 파일명 지원
            encoded_filename = os.path.basename(file_path).encode('utf-8').decode('latin-1')
            response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
            return response
        except Exception as e:
            messages.error(request, f"파일 다운로드 중 오류가 발생했습니다: {e}")
    else:
        messages.error(request, "생성된 PPT 파일이 저장소에 존재하지 않습니다.")
    
    return redirect('home')