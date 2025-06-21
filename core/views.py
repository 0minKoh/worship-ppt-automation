from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required # 로그인한 사용자만 접근 가능
def home(request):
    # 현재 로그인한 사용자 정보 (request.user)를 템플릿으로 전달할 수 있습니다.
    context = {
        'username': request.user.username,
        'is_media_team': request.user.groups.filter(name='미디어팀').exists(),
        'is_worship_prep_team': request.user.groups.filter(name='예배준비팀').exists(),
        'is_praise_team': request.user.groups.filter(name='찬양팀').exists(),
        'is_member': request.user.groups.filter(name='교인').exists(),
    }
    return render(request, 'core/home.html', context)
