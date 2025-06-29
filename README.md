# 🚀 예배 PPT 자동화 관리 시스템 (Worship PPT Automation System)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/Django-~5.0-green?logo=django)](https://www.djangoproject.com/)

---

## 💡 개요 (Overview)

본 프로젝트는 수동적인 예배용 PowerPoint (PPT) 제작 과정에서 발생하는 비효율성 및 인적 자원 소모 문제를 해결하기 위해 개발된 **Django 기반의 웹 애플리케이션**입니다. 예배 관련 정보(찬양, 설교, 광고 등)를 통합 관리하고, 최신 기술을 활용하여 PPT 제작을 자동화함으로써 교회의 미디어 사역 효율성을 극대화합니다.

이 시스템은 단순한 자동화를 넘어, 사용자가 직관적으로 정보를 입력하고 실시간으로 작업 진행 상황을 모니터링할 수 있는 사용자 친화적인 인터페이스를 제공하여, 예배 준비의 디지털 전환을 지원합니다.

**핵심 가치 제안:** 생산성 향상, 작업 표준화, 수동 오류 감소, 유저 경험 개선.

---

### 서비스 주요 흐름 (Service Workflow Overview)

본 시스템은 사용자가 예배 정보를 입력하고 PPT를 자동으로 생성하는 과정을 효율적으로 지원합니다.

1.  **메인 대시보드:**
    사용자는 로그인 후 메인 대시보드에서 다가오는 주일 예배의 PPT 제작 현황을 한눈에 파악할 수 있습니다. 각 팀의 역할에 따라 필요한 정보 입력 버튼이 조건부로 활성화됩니다.

    ![예배 PPT 자동화 시스템 메인 대시보드](/docs/img/worship_ppt_dashboard.png)
    *이미지 설명: 서비스의 핵심 기능들을 한눈에 볼 수 있는 메인 대시보드 화면입니다. 이번 주 주일 예배 현황, 역할별 접근 가능한 버튼, 그리고 PPT 제작 진행 상황 메시지가 실시간으로 업데이트되는 모습을 담고 있습니다.*

2.  **예배 정보 입력:**
    '예배준비팀' 또는 '미디어팀'은 예배 정보 입력 페이지를 통해 설교자, 설교 제목, 성경 본문 범위(유효성 검사 포함), 광고 담당자 등 예배의 필수 정보를 입력합니다.
    
    ![예배 정보 입력 폼](/docs/img/worship_info_form.png)
    *이미지 설명: 예배 정보를 입력하는 폼 화면입니다. 설교자, 설교 제목, 성경 본문 범위 등 주일 예배의 주요 정보들을 입력할 수 있습니다. 특히 성경 본문 범위는 잘못된 형식 입력 시 실시간으로 유효성 검사 오류를 표시합니다.*

3.  **찬양 정보 입력:**
    '찬양팀' 또는 '미디어팀'은 찬양 정보 입력 페이지에서 예배에 사용될 찬양들의 제목과 가사 출처 URL을 입력합니다. 드래그앤드롭을 통해 찬양 순서를 직관적으로 변경할 수 있으며, 결단 찬양은 예배당 하나만 지정되도록 유효성 검사가 적용됩니다.
    
    ![찬양 정보 입력 폼](/docs/img/song_info_form.png)
    *이미지 설명: 찬양 정보를 입력하는 폼 화면입니다. 찬양 제목, 가사 출처 URL, 결단 찬양 여부를 입력하며, 드래그앤드롭으로 찬양 순서를 쉽게 변경할 수 있습니다. 결단 찬양 중복 선택 시 즉각적인 유효성 검사 오류가 표시됩니다.*

4.  **PPT 제작 시작 및 실시간 모니터링:**
    모든 필수 정보(예배, 찬양, 광고)가 입력되면 '미디어팀'은 'PPT 제작 시작' 버튼을 통해 PPT 생성을 요청합니다. 이 과정은 Celery 백그라운드 태스크로 비동기적으로 처리되며, 메인 대시보드에서 AI가 '생각하는 과정'처럼 상세 진행 상황 메시지를 실시간으로 모니터링할 수 있습니다.
    
    ![PPT 제작 시작 확인 페이지](/docs/img/ppt_start_page.png)
    *이미지 설명: PPT 제작을 시작하기 전, 최종 정보를 확인하고 제작을 요청하는 페이지입니다. '제작 시작하기' 버튼을 클릭하면 Celery 태스크가 트리거됩니다.*

    <video style="width: 100%;" src="/docs/img/ppt_progress_status.mov" controls muted>
    이 브라우저는 동영상을 지원하지 않습니다.
    </video>
    *이미지 설명: PPT 제작이 진행될 때 메인 대시보드에 표시되는 실시간 진행 상황 메시지입니다. AI가 생각하는 것처럼 메시지가 순차적으로 누적되며, 이후 실제 Celery 태스크의 진행 메시지로 전환됩니다.*

5.  **PPT 다운로드:**
    PPT 제작이 완료되면 사용자에게 알림이 전송되고, 'PPT 다운로드' 버튼이 활성화됩니다. 사용자는 클릭 한 번으로 최종 생성된 PPT 파일을 다운로드할 수 있습니다.

    ![PPT 다운로드 완료 화면](/docs/img/ppt_download_complete.png)
    *이미지 설명: PPT 제작이 성공적으로 완료된 후 활성화되는 다운로드 버튼과 완료 알림 메시지입니다. 사용자가 클릭하여 생성된 PPT 파일을 즉시 다운로드할 수 있습니다.*


---

## ✨ 주요 기능 및 기술 (Key Features & Technical Contributions)

### 1. 역할 기반 접근 제어 및 사용자 관리
* **설명:** Django의 강력한 내장 인증 시스템과 `Group` 모델을 활용하여 **`미디어팀`, `찬양팀`, `예배준비팀`, `교인`** 등 4가지 주요 사용자 역할에 따른 세분화된 접근 권한을 구현했습니다. 커스텀 데코레이터를 개발하여 특정 페이지 및 기능에 대한 접근을 역할에 따라 동적으로 제어하며, 특히 `미디어팀`에게는 모든 관리 기능에 대한 포괄적인 접근 권한을 부여했습니다.
* **기술적 장점:** 보안 및 권한 관리 시스템 설계 역량, Django 인증 시스템의 깊은 이해 및 확장성 있는 활용.
* **기타:** 팀별 업무 분담을 명확히 하고, 중요 데이터 및 기능에 대한 비인가 접근을 효과적으로 차단하여 시스템의 안정성을 높였습니다.

### 2. 데이터 모델 및 API 설계
* **설명:** 예배(`WorshipInfo`), 찬양(`SongInfo`), PPT 요청(`PptRequest`), 템플릿(`PptTemplate`) 등 핵심 비즈니스 도메인을 반영하는 **Django 데이터 모델(`models.py`)을 설계하고 구현**했습니다. 특히, `SongInfo` 모델에서는 `can_order=True` 설정과 `UniqueConstraint`를 `condition=Q()`와 결합하여 다음과 같은 복잡한 비즈니스 규칙을 데이터베이스 레벨에서 강제했습니다:
    * **찬양 순서 자동 부여 및 드래그앤드롭 정렬:** 사용자가 직접 순서를 입력하는 대신, 추가 순서대로 자동 할당되며 UI에서 드래그앤드롭으로 쉽게 순서를 변경할 수 있습니다.
    * **결단 찬양 유일성:** 각 예배당 **오직 하나의 결단 찬양만** 존재하도록 데이터 무결성 제약 조건을 구현하여 데이터의 일관성을 확보했습니다.
* **기술적 장점:** 관계형 데이터베이스(PostgreSQL) 설계 능력, Django ORM의 고급 기능(`UniqueConstraint`, `Q` 객체, `Formset`) 활용, 데이터 무결성 및 일관성 확보.
* **참고:** 데이터의 정확성과 신뢰성을 보장하고, 복잡한 비즈니스 규칙을 시스템적으로 반영하여 휴먼 에러를 최소화했습니다.

![관계형 데이터베이스 스키마 이미지]
*이미지 설명: 핵심 데이터 모델인 `WorshipInfo`, `SongInfo`, `PptRequest`, `PptTemplate` 및 Django 내장 인증 모델(`auth_user`, `auth_group`) 간의 관계를 시각화한 ERD입니다. 각 테이블의 필드와 외래 키 관계가 명확하게 표현되어 있습니다.*

### 3. 지능형 콘텐츠 처리 및 자동화된 PPT 생성 파이프라인
* **기여:**
    * **웹 크롤링:** `BeautifulSoup4`와 `Requests`를 활용하여 Bugs Music과 같은 외부 음원 사이트에서 찬양 가사를 안정적으로 추출하고, 추출된 텍스트에서 불필요한 문자열(`_x000D_` 등)을 정제하는 로직을 구현했습니다.
    * **LLM 기반 가사/텍스트 가공:** **Google Gemini API (`google-genai` 라이브러리 및 Pydantic 모델)**를 사용하여, 크롤링된 방대한 가사를 PPT 슬라이드에 적합한 분량(3-4줄, 1줄당 15자 내외)으로 자동 분할하고, **연속되는 후렴구 등 중복 슬라이드를 제거**하는 정교한 후처리 로직을 개발했습니다.
    * **성경 구절 파서:** 로컬에 저장된 `EUC-KR` 인코딩 성경 TXT 파일에서, 특정 범위의 구절을 정확히 추출하고 파싱하는 로직을 직접 구현했습니다. (다양한 인코딩 및 텍스트 구조 처리 능력)
    * **PPT 자동 생성:** `python-pptx` 라이브러리를 활용하여, 위에서 가공된 예배 정보(설교자, 제목, 본문, 기도자, 봉헌자, 광고, 축도자)와 찬양/성경 가사를 동적으로 PPT 슬라이드에 삽입하고, 슬라이드 순서 및 개수를 유연하게 조작하는 복잡한 PPT 생성 로직을 설계 및 구현했습니다. 특히, `_insert_slide_at_index`와 같은 내부 XML 조작을 통해 정확한 위치에 슬라이드를 삽입하는 고도화된 방식을 적용했습니다.
* **기술적 장점:** 비정형/외부 데이터를 정형화된 비즈니스 데이터로 가공하는 능력, LLM을 활용한 콘텐츠 최적화, `python-pptx`의 심층 활용, 복잡한 문자열 및 인코딩 문제 해결 역량.
* **비즈니스 문제 해결:** 예배 PPT 제작에 소요되던 수작업 시간(가사 복사, 분할, 서식 조정)을 획기적으로 단축하고, PPT의 가독성 및 디자인 표준화를 달성했습니다.

![예배 정보 입력 폼 이미지]
*이미지 설명: 예배 정보를 입력하는 폼 화면입니다. 설교자, 설교 제목, 성경 본문 범위 등 주일 예배의 주요 정보들을 입력할 수 있습니다. 성경 본문 범위는 잘못된 형식 입력 시 실시간으로 유효성 검사 오류를 표시합니다.*

![찬양 정보 입력 폼 이미지]
*이미지 설명: 찬양 정보를 입력하는 폼 화면입니다. 찬양 제목, 가사 출처 URL, 결단 찬양 여부를 입력하며, 드래그앤드롭으로 찬양 순서를 쉽게 변경할 수 있습니다. 결단 찬양 중복 선택 시 즉각적인 유효성 검사 오류가 표시됩니다.*

### 4. 고성능 비동기 작업 처리 및 실시간 모니터링
* **기여:**
    * `Celery`를 핵심 작업 큐로, `Redis`를 메시지 브로커로 활용하여 PPT 생성과 같은 장시간 소요 작업을 백그라운드에서 비동기적으로 처리하는 아키텍처를 구축했습니다. 이를 통해 웹 애플리케이션의 응답성을 유지하고 사용자 UI 블로킹을 방지했습니다.
    * **AJAX 폴링 및 AI 스타일 진행 메시지:** Django 백엔드(`PptRequest` 모델 및 상태 API)와 프론트엔드(`AJAX 폴링` 및 JavaScript)를 연동하여 Celery 태스크의 진행 상태(예: '크롤링 중...', '분할 중...', '완료')를 사용자에게 실시간으로 업데이트하여 보여주는 기능을 구현했습니다. 특히, 초기 API 호출을 최적화하기 위해 **시뮬레이션된 '생각하는 과정' 메시지 시퀀스**를 도입하여 사용자 경험을 개선했습니다.
    * **작업 완료/실패 알림:** 작업 완료 또는 실패 시 사용자에게 브라우저 `alert`를 통해 즉각적으로 알림을 제공하여, 작업의 신뢰성과 투명성을 높였습니다.
* **기술적 장점:** 비동기 시스템 설계 및 구현 능력, 실시간 데이터 통신 및 UI/UX 설계 역량, 백그라운드 작업의 안정적인 관리.
* **비즈니스 문제 해결:** 사용자 대기 시간 감소, 작업 진행 상황에 대한 투명한 정보 제공, 시스템 전반의 효율성 향상.

![PPT 제작 진행 상황 이미지]
*이미지 설명: PPT 제작이 진행될 때 메인 대시보드에 표시되는 실시간 진행 상황 메시지입니다. AI가 생각하는 것처럼 메시지가 순차적으로 누적되며, 이후 실제 Celery 태스크의 진행 메시지로 전환됩니다.*

![PPT 다운로드 완료 화면 이미지]
*이미지 설명: PPT 제작이 성공적으로 완료된 후 활성화되는 다운로드 버튼과 완료 알림 메시지입니다. 사용자가 클릭하여 생성된 PPT 파일을 즉시 다운로드할 수 있습니다.*

---

## 🛠️ 기술 스택 (Technologies Used)

* **Backend Framework:** `Python`, `Django`
* **Database:** `PostgreSQL`
* **Asynchronous Tasks:** `Celery`, `Redis` (Message Broker)
* **LLM Integration:** `google-genai` (Google Gemini API), `Pydantic` (for structured output)
* **Web Scraping:** `BeautifulSoup4`, `Requests`
* **PPT Automation:** `python-pptx`
* **Deployment:** `Render` (PaaS), `Persistent Disk` (for media files)
* **Web Server (Prod):** `Gunicorn`
* **Version Control:** `Git`, `GitHub`

---

## 🚀 설치 및 실행 (Setup & Run)

프로젝트를 로컬 환경에서 실행하기 위한 단계별 지침입니다.

1.  **리포지토리 클론:**
    ```bash
    git clone [Your-GitHub-Repo-URL]
    cd worship_ppt_automation
    ```

2.  **가상 환경 설정 및 활성화:**
    ```bash
    python -m venv venv
    source venv/bin/activate # macOS/Linux
    # .venv\Scripts\Activate.ps1 # Windows PowerShell
    ```

3.  **의존성 설치:**
    ```bash
    pip install -r requirements.txt
    ```
    (requirements.txt 파일은 `pip freeze > requirements.txt`로 생성하거나, 위에서 언급된 라이브러리들을 수동으로 설치합니다.)

4.  **.env 파일 설정:**
    프로젝트 루트 디렉토리(`.git` 폴더가 있는 곳)에 `.env` 파일을 생성하고, 다음 내용을 채워 넣습니다. **`[...]` 부분은 실제 값으로 변경해야 합니다.**
    ```ini
    # .env

    SECRET_KEY='[Django SECRET_KEY - 예: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"]'
    DEBUG=True
    ALLOWED_HOSTS='localhost,127.0.0.1'

    DATABASE_URL='postgres://worship_ppt_app_user:your_secure_password_for_worship_app@localhost:5432/worship_ppt_db'
    CELERY_BROKER_URL='redis://localhost:6379/0'
    GEMINI_API_KEY='[당신의 Google Gemini API 키]'
    ```

5.  **PostgreSQL 및 Redis 서버 실행:**
    로컬에 PostgreSQL과 Redis가 설치되어 있어야 합니다. (Homebrew 등으로 설치 권장)
    ```bash
    brew services start postgresql@14
    brew services start redis
    ```
    PostgreSQL에 `worship_ppt_db` 데이터베이스와 `worship_ppt_app_user` 역할을 생성해야 합니다. (`psql`로 접속 후 `CREATE DATABASE worship_ppt_db OWNER worship_ppt_app_user;` 등)

6.  **Django 데이터베이스 마이그레이션:**
    ```bash
    python manage.py makemigrations core
    python manage.py migrate
    ```

7.  **Django 슈퍼유저 생성:**
    ```bash
    python manage.py createsuperuser
    ```

8.  **로컬 성경 파일 준비:**
    프로젝트 루트의 `core/data/bible_text/` 경로에 `EUC-KR` 인코딩으로 저장된 모든 성경 TXT 파일(`1-01창세기.txt` 등)을 넣어주세요.

9.  **Django 개발 서버 실행:**
    ```bash
    python manage.py runserver
    ```http://127.0.0.1:8000/`에서 접속 가능합니다.

10. **Celery 워커 실행 (새 터미널/탭):**
    ```bash
    source venv/bin/activate # 가상 환경 활성화
    # 로케일 및 인코딩 환경 변수 설정 (중요: 한글 처리 오류 방지)
    export LANG="ko_KR.UTF-8"
    export LC_ALL="ko_KR.UTF-8"
    export PYTHONIOENCODING="utf-8"
    export PYTHONUNBUFFERED=1
    # Celery 워커 시작
    celery -A worship_ppt_automation worker -l info
    ```

---

## ☁️ 배포 (Deployment)

본 프로젝트는 **Render (PaaS)** 클라우드 플랫폼에 배포될 예정입니다.

* **플랫폼:** Render Web Services (Django Web), Render Background Workers (Celery Worker), Render Redis (for Celery broker), Render PostgreSQL.
* **전략:**
    * **Git 통합 배포:** 로컬 Docker Desktop 설치 없이, GitHub 리포지토리를 Render에 연결하여 코드를 직접 빌드하고 배포합니다.
    * **영구 디스크 활용:** S3와 같은 외부 스토리지를 사용하지 않고, Render가 제공하는 영구 디스크(`/var/data/media`)에 사용자가 업로드하는 미디어 파일(PPT 템플릿, 생성된 PPT)을 저장하여 배포 간에도 데이터가 유지되도록 합니다.
    * **서비스 분리:** Django 웹 애플리케이션과 Celery 워커를 별도의 Render 서비스로 배포하여 독립적인 스케일링 및 관리가 가능하도록 `Procfile`을 구성했습니다.
    * **환경 변수 관리:** 모든 민감한 설정(API 키, DB 자격 증명 등)은 Render 대시보드의 환경 변수 관리 기능을 통해 안전하게 주입합니다.
* **Procfile:**
    ```
    web: gunicorn worship_ppt_automation.wsgi --log-file - --workers 2 --bind 0.0.0.0:$PORT
    worker: celery -A worship_ppt_automation worker -l info --concurrency 2
    ```

---

## 🚀 향후 개선 방향 (Future Enhancements)

* **WebSocket 기반 실시간 진행 상황:** 현재 AJAX 폴링을 Django Channels와 같은 WebSocket 기술로 전환하여 더욱 즉각적인 실시간 업데이트 및 양방향 통신 구현.
* **LLM을 이용한 설교 요약/광고 초안 생성:** 목사님 설교 초고나 광고 요청 텍스트를 LLM으로 분석하여 PPT용 요약/초안을 자동으로 제안하는 기능 추가.
* **고급 PPT 템플릿 관리:** Django Admin에서 PPT 템플릿의 슬라이드 레이아웃별 Placeholder 매핑을 직접 관리할 수 있는 기능 개발.
* **사용자 친화적인 회원가입/비밀번호 찾기 페이지:** Django 기본 Admin 대신 커스텀 폼과 뷰를 이용한 웹 UI 구현.
* **알림 시스템 고도화:** 브라우저 푸시 알림 API (Service Worker) 또는 Firebase Cloud Messaging(FCM)을 통한 푸시 알림 구현.
