# worship_ppt_automation/worship_ppt_automation/celery.py

import os
from celery import Celery

# Django 설정 모듈을 Celery에 알려줍니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worship_ppt_automation.settings')

# 'worship_ppt_automation' 이라는 이름으로 Celery 앱을 생성합니다.
app = Celery('worship_ppt_automation')

# Django의 settings.py에서 Celery 관련 설정을 가져옵니다.
# 'CELERY_'로 시작하는 모든 설정은 Celery 설정으로 간주됩니다.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 등록된 모든 Django 앱에서 tasks.py 파일을 자동으로 찾아서 Celery 태스크로 등록합니다.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')