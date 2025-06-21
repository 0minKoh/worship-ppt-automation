# Django 예배 PPT 자동화 프로그램 설계

### 1. 프로젝트 개요 및 목표 재확인

- **이름:** 예배 PPT 자동화 관리 시스템 (Worship PPT Automation System)
- **목표:** 예배 관련 정보(찬양, 설교, 광고 등)를 입력받아 자동으로 예배용 PowerPoint(PPT) 파일을 생성하고 관리하는 웹 기반 툴.
- **핵심 기능:**
  - 역할 기반 사용자 관리 및 접근 제어
  - 예배 및 찬양 정보 입력/관리
  - 찬양 가사 웹 크롤링 및 LLM(Gemini API)을 통한 가사/설교 내용 가공
  - python-pptx를 이용한 PPT 자동 생성
  - Celery/Redis를 활용한 PPT 생성 비동기 처리 및 진행 상황 알림
  - 생성된 PPT 다운로드

### 2. 주요 아키텍처 및 기술 스택

- **웹 프레임워크:** Django
- **데이터베이스:** PostgreSQL
- **비동기 작업 큐:** Celery
- **메시지 브로커:** Redis
- **웹 스크래핑:** BeautifulSoup4 (bs4)
- **LLM 연동:** Google Gemini API
- **PPT 생성:** python-pptx
- **파일 저장:** Django FileField (로컬 파일 시스템 또는 클라우드 스토리지 연동 고려)
- **프론트엔드:** Django Template (HTML, CSS, JavaScript)
- **실시간 통신 (선택적/확장):** Django Channels (WebSockets for real-time progress)
- **웹 푸시 알림:** Django Signals와 Web Push API 연동 (또는 Firebase Cloud Messaging)

### 3. 데이터베이스 설계 (ERD 기반)

<br>
<img src="./img/250621_ERD.png">
<br>
<br>

- **Auth_User & Auth_Group (Django 내장):** 사용자 인증 및 역할(미디어팀, 찬양팀 등) 관리. Auth_User_Groups를 통해 다대다 관계 형성.
- **WorshipInfo (예배 정보):** 예배 날짜, 종류, 설교자, 제목, 본문, 광고, 기도 제목 등 핵심 예배 정보.
  - **관계:** created_by (FK to Auth_User), SongInfo (1:N), PptRequest (1:1).
- **SongInfo (찬양 정보):** 특정 예배에 속하는 찬양의 정보 (제목, YouTube URL, 가사, 페이지별 가사).
  - **관계:** worship_info (FK to WorshipInfo, CASCADE delete), created_by (FK to Auth_User).
- **PptRequest (PPT 제작 요청):** 특정 예배의 PPT 제작 요청 상태, 생성된 파일, Celery 작업 ID, 진행 메시지 등을 기록.
  - **관계:** worship_info (1:1 FK to WorshipInfo, CASCADE delete), requested_by (FK to Auth_User).
- **PptTemplate (PPT 템플릿):** 사용자가 업로드하고 관리할 수 있는 PPTX 템플릿 파일.
  - **관계:** created_by (FK to Auth_User).

### 4. 주요 유즈케이스별 사용자 흐름 및 기능 설계

#### 4.1. 사용자 인증 및 역할 기반 접근 제어

- **로그인/로그아웃:** Django 기본 인증 시스템 사용 (`/accounts/login/`, `/accounts/logout/`).
- **역할 정의:** Django Admin에서 `미디어팀`, `찬양팀`, `예배준비팀`, `교인` 그룹 생성.
- **사용자 역할 할당:** Django Admin 또는 사용자 관리 페이지에서 사용자에게 해당 그룹 할당.
- **접근 제어:**
  - **미디어팀:** 모든 기능 접근.
  - **찬양팀:** 찬양 정보 입력/수정, PPT 제작 현황 조회.
  - **예배준비팀:** 예배 정보 입력/수정, PPT 제작 현황 조회.
  - **교인:** PPT 제작 현황 조회.
  - **구현:** Django `@login_required` 데코레이터와 커스텀 권한 데코레이터/믹스인 (`@group_required` 등) 사용.

#### 4.2. 메인 페이지 대시보드

- **현황 표시:** 현재 주간의 예배 PPT 제작 현황 (PptRequest 모델의 status 기반).
- **역할별 버튼 노출:**
  - **미디어팀:** 'PPT 제작 시작' 버튼 (PPT 미완성 시), 기타 관리 버튼.
  - **찬양팀:** '찬양 정보 입력' 버튼 (찬양 정보 미입력 시).
  - **예배준비팀:** '예배 정보 입력' 버튼 (예배 정보 미입력 시).
- **구현:** Django View에서 `request.user`의 그룹 정보를 확인하여 템플릿에서 조건부 렌더링.

#### 4.3. 정보 입력 페이지

- **예배 정보 입력/수정 (WorshipInfoForm):**
  - 설교자, 제목, 본문, 광고, 기도 제목 등 입력 폼.
  - LLM 처리 여부 플래그 (`is_llm_processed`) 활용.
- **찬양 정보 입력/수정 (SongInfoForm):**
  - 제목, YouTube URL, 순서 등 입력 폼.
  - 특정 WorshipInfo에 연결.
- **구현:** Django ModelForm 활용하여 CRUD(Create, Read, Update, Delete) 뷰 개발.

#### 4.4. PPT 제작 및 진행 상황 모니터링

- **PPT 제작 시작 페이지 (미디어팀 전용):**
  - 찬양/예배 정보 최종 확인 및 수정 기능 제공.
  - 'PPT 제작 시작' 버튼 클릭 시 Celery 작업 시작.
- **비동기 처리:** Celery 태스크로 PPT 제작 로직을 분리.
  - **Task 1: 예배 정보 LLM 처리:** (`WorshipInfo`의 `is_llm_processed`가 `False`인 경우) Gemini API로 설교/광고/기도 제목 등을 항목별로 정리.
  - **Task 2: 찬양 가사 크롤링 및 LLM 처리:** `SongInfo`의 `youtube_url`에서 bs4로 가사 크롤링. 크롤링된 가사를 Gemini API로 페이지별 적절한 길이로 분할하여 `lyrics_pages` 필드에 저장.
  - **Task 3: PPT 생성:** python-pptx를 사용하여 미리 정의된 PptTemplate에 따라 PPT 파일 생성. WorshipInfo와 SongInfo의 처리된 데이터를 활용.
- **실시간 진행 상황:**
  - PPT 제작 페이지에서 백엔드 진행 상황 (`progress_message`)을 사용자에게 실시간으로 업데이트하여 표시. (예: "찬양 가사 크롤링 중...", "예배 정보 AI 정리 중...", "PPT 파일 생성 중...").
  - **구현:** AJAX 폴링 (주기적인 서버 요청) 또는 WebSockets (Django Channels) 고려.
- **알림 및 다운로드:**
  - PPT 제작 완료 시 Web Push 알림.
  - 다운로드 버튼 활성화 (PptRequest의 generated_ppt_file 필드 사용).

### 5. 배포 전략 (고려 사항)

- **환경 변수 관리:** django-environ 또는 유사한 라이브러리를 사용하여 민감 정보(API 키, DB 비밀번호)를 코드 외부에서 관리.
- **정적/미디어 파일 서빙:** 개발 시 Django가 처리하지만, 배포 시에는 Nginx 또는 클라우드 스토리지(AWS S3 등)를 사용하여 효율적으로 서빙.
- **WSGI 서버:** Gunicorn 등 사용.
- **Supervisor/Systemd:** Celery 워커 프로세스 및 Redis/PostgreSQL 서버를 안정적으로 관리.
