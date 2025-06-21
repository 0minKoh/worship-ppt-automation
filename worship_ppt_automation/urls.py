from django.contrib import admin
from django.urls import path, include

# Only Development settings
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls'))
]


# 개발 환경에서만 미디어 파일을 서빙하도록 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)