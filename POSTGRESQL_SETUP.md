# PostgreSQL 설치 가이드 (Windows)

## Phase 1 완료 상태

✅ **완료된 작업:**
- Poetry 프로젝트 초기화 완료
- FastAPI 핵심 파일 생성 (main, config, security)
- 데이터베이스 모델 생성 (User, Team, UserSettings, AnalysisJob, AnalysisResult)
- 인증 API 구현 (회원가입, 로그인, 사용자 정보 조회)
- 설정 API 구현 (테마, 워크스페이스, 유틸 설정 관리)
- Pydantic 스키마 정의
- JWT 인증 및 의존성 시스템

⚠️ **대기 중:**
- PostgreSQL 설치 및 데이터베이스 생성
- 서버 재시작 및 테스트

---

## PostgreSQL 16 수동 설치

### 1단계: PostgreSQL 다운로드

1. 공식 웹사이트 방문:
   - https://www.postgresql.org/download/windows/

2. **EDB Installer** 다운로드 (권장):
   - https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
   - PostgreSQL 16.x for Windows x86-64 다운로드

### 2단계: 설치 실행

1. 다운로드한 설치 파일 실행 (관리자 권한)

2. 설치 옵션:
   - **Installation Directory**: 기본값 사용 (`C:\Program Files\PostgreSQL\16`)
   - **Components**: 모두 선택 (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
   - **Data Directory**: 기본값 사용 (`C:\Program Files\PostgreSQL\16\data`)
   - **Password**: `postgres123` (개발용, 프로덕션에서는 강력한 비밀번호 사용)
   - **Port**: `5432` (기본값)
   - **Locale**: `[Default locale]`

3. 설치 진행 (약 2-3분 소요)

4. 설치 완료 후 **Stack Builder** 실행 창이 나타나면 "Skip" 선택

### 3단계: PostgreSQL 서비스 확인

1. Windows 서비스 확인:
   ```powershell
   # PowerShell 실행 (관리자 권한)
   Get-Service postgresql*
   ```

   또는 **작업 관리자** → **서비스** 탭에서 `postgresql-x64-16` 서비스가 "실행 중"인지 확인

2. PostgreSQL이 시작되지 않았다면:
   ```powershell
   Start-Service postgresql-x64-16
   ```

### 4단계: 데이터베이스 생성

1. **pgAdmin 4** 실행 (시작 메뉴에서 검색)

2. 왼쪽 패널에서 **Servers** → **PostgreSQL 16** → **Databases** 우클릭

3. **Create** → **Database** 선택

4. 데이터베이스 정보 입력:
   - **Database**: `analysisdb`
   - **Owner**: `postgres`
   - **Encoding**: `UTF8`
   - **Save** 클릭

#### 또는 명령줄로 생성:

```bash
# psql 명령줄 도구 실행 (비밀번호: postgres123)
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE analysisdb
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    CONNECTION LIMIT = -1;

# 종료
\q
```

### 5단계: 연결 테스트

1. 백엔드 디렉토리로 이동:
   ```bash
   cd D:\___POCUtilWebServer_Claude\backend
   ```

2. FastAPI 서버 시작:
   ```bash
   poetry run uvicorn api.main:app --reload
   ```

3. 성공 메시지 확인:
   ```
   ✓ Analysis Tool API v1.0.0 started
   ✓ Database initialized
   ✓ API docs available at: /api/docs
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

4. 브라우저에서 API 문서 확인:
   - http://127.0.0.1:8000/api/docs

---

## 대체 방법: Docker 사용 (Phase 5로 건너뛰기)

PostgreSQL 설치가 어려운 경우, Docker를 사용하여 개발 환경을 구축할 수 있습니다:

### 전제 조건:
- Docker Desktop for Windows 설치 (https://www.docker.com/products/docker-desktop/)

### 간단한 PostgreSQL 컨테이너 실행:

```bash
# PostgreSQL 16 컨테이너 실행
docker run -d \
  --name postgres-dev \
  -e POSTGRES_PASSWORD=postgres123 \
  -e POSTGRES_DB=analysisdb \
  -p 5432:5432 \
  postgres:16-alpine

# 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs postgres-dev
```

이후 FastAPI 서버를 시작하면 자동으로 연결됩니다.

---

## 환경 변수 설정 (.env)

`.env` 파일이 이미 생성되어 있습니다:

```env
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/analysisdb
```

만약 다른 비밀번호를 사용했다면 `.env` 파일을 수정하세요:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/analysisdb
```

---

## 문제 해결

### PostgreSQL 서비스가 시작되지 않는 경우:

1. **이벤트 뷰어** 확인 (Windows + X → 이벤트 뷰어)
2. **Windows 로그** → **응용 프로그램**에서 PostgreSQL 관련 오류 확인
3. 포트 5432가 이미 사용 중인지 확인:
   ```powershell
   netstat -ano | findstr :5432
   ```

### psql 명령을 찾을 수 없는 경우:

PostgreSQL bin 디렉토리를 PATH에 추가:

```powershell
# PowerShell (관리자 권한)
[Environment]::SetEnvironmentVariable(
    "Path",
    "$env:Path;C:\Program Files\PostgreSQL\16\bin",
    [System.EnvironmentVariableTarget]::Machine
)
```

---

## 다음 단계

PostgreSQL 설치 및 데이터베이스 생성이 완료되면:

1. FastAPI 서버 재시작
2. API 문서에서 회원가입/로그인 테스트 (http://127.0.0.1:8000/api/docs)
3. Phase 2로 진행: PyQt 분석 로직 통합

---

**궁금한 점이 있으시면 언제든지 질문해주세요!**
