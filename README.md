# POC Util WebServer

PyQt/PySide 기반 Python 분석 도구를 현대적인 웹 애플리케이션으로 전환하는 프로젝트

## 프로젝트 개요

**목표**: 로컬 Python 분석 도구를 팀 단위(10-50명)가 사용할 수 있는 웹 애플리케이션으로 전환
- Python 분석 코드는 그대로 재사용
- 빠른 처리(<1분) 작업에 최적화
- React SPA 기반 현대적인 UI/UX

## 기술 스택 (2026년 최신)

### 백엔드
- **FastAPI** (Python 3.12): 비동기 네이티브, 자동 API 문서화
- **PostgreSQL 16**: 데이터베이스
- **Redis 7**: 캐싱 및 세션 관리
- **Poetry**: 의존성 관리

### 프론트엔드
- **React 18+**: UI 라이브러리
- **Vite 5**: 빌드 도구 (초고속 HMR)
- **TypeScript 5.4**: 타입 안정성
- **TanStack Query v5**: 서버 상태 관리
- **Zustand**: 클라이언트 상태 관리

### 인프라
- **Docker Compose**: 개발 환경 오케스트레이션
- **nginx**: 리버스 프록시
- **GitHub Actions**: CI/CD 자동화

## 프로젝트 구조

```
POCUtilWebServer/
├── backend/              # FastAPI 백엔드
│   ├── analysis/        # 분석 코어 로직
│   └── api/             # API 엔드포인트
├── frontend/            # React 프론트엔드
│   └── src/
├── nginx/               # nginx 설정
├── docker-compose.yml   # Docker 오케스트레이션
└── README.md
```

## 빠른 시작

### 1. PostgreSQL 설치

먼저 PostgreSQL을 설치하고 데이터베이스를 생성하세요:

**상세 가이드:** [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

```bash
# 요약:
# 1. PostgreSQL 16 설치 (https://www.postgresql.org/download/windows/)
# 2. 데이터베이스 생성 (analysisdb)
# 3. 비밀번호 설정 (postgres123 권장 - 개발용)
```

### 2. 백엔드 실행

```bash
cd backend

# 의존성 설치 (최초 1회)
poetry install

# FastAPI 서버 시작
poetry run uvicorn api.main:app --reload
```

성공 메시지:
```
✓ Analysis Tool API v1.0.0 started
✓ Database initialized
✓ API docs available at: /api/docs
INFO: Uvicorn running on http://127.0.0.1:8000
```

### 3. API 테스트

**Swagger UI (권장):**
- http://127.0.0.1:8000/api/docs

**테스트 스크립트:**
```bash
cd backend
poetry run python test_api.py
```

### 프론트엔드 (Phase 4에서 구현 예정)

```bash
cd frontend
npm install
npm run dev
```

### Docker 환경 (Phase 5에서 구성 예정)

```bash
# 전체 스택 실행
docker-compose up -d

# 접속
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 구현 계획

상세한 구현 계획은 [여기](./.claude/plans/serialized-petting-falcon.md)를 참조하세요.

### 구현 단계

- [x] Phase 0: GitHub 레포지토리 초기화
- [x] **Phase 1: FastAPI 백엔드 기반 구축** ✅
- [ ] Phase 2: PyQt 분석 로직 통합 (다음 단계 🚧)
- [ ] Phase 3: REST API 및 WebSocket 개발
- [ ] Phase 4: React SPA 프론트엔드 개발
- [ ] Phase 5: Docker 환경 구성
- [ ] Phase 6: 통합 테스트 및 검증

### Phase 1 완료 사항 ✅

**구현된 기능:**
- ✅ Poetry 프로젝트 초기화 및 의존성 설치
- ✅ FastAPI 핵심 파일 (config, security, dependencies)
- ✅ 데이터베이스 모델 5개 (User, Team, UserSettings, AnalysisJob, AnalysisResult)
- ✅ 인증 API (회원가입, 로그인, 사용자 정보)
- ✅ 설정 API (테마, 워크스페이스, 유틸 설정 관리)
- ✅ Pydantic 스키마 정의
- ✅ JWT 인증 시스템 (Argon2 해싱)

**문서:**
- 📄 [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md) - 완료 내역 상세
- 📄 [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - PostgreSQL 설치 가이드

**⚠️ 다음 단계:** PostgreSQL 설치 후 서버 시작 및 테스트

## API 엔드포인트

### 인증 (✅ 구현됨)
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인 (OAuth2 Form)
- `POST /api/v1/auth/login/json` - 로그인 (JSON)
- `GET /api/v1/auth/me` - 현재 사용자 정보

### 설정 (✅ 구현됨)
- `GET /api/v1/settings` - 사용자 설정 조회
- `PATCH /api/v1/settings` - 사용자 설정 업데이트 (부분)
- `PATCH /api/v1/settings/theme?theme=<light|dark>` - 테마 변경
- `PATCH /api/v1/settings/workspace` - 워크스페이스 상태 저장
- `PATCH /api/v1/settings/tool-preferences` - 유틸별 설정 저장
- `POST /api/v1/settings/recent-tool/{tool_id}` - 최근 사용 유틸 추가

### 분석 (Phase 3에서 구현 예정)
- `POST /api/v1/analysis/upload` - 파일 업로드
- `POST /api/v1/analysis/start` - 분석 시작
- `GET /api/v1/analysis/{job_id}/status` - 상태 조회
- `GET /api/v1/analysis/{job_id}/result` - 결과 다운로드
- `GET /api/v1/analysis/history` - 이력 조회

### WebSocket (Phase 3에서 구현 예정)
- `WS /ws/analysis/{job_id}` - 실시간 진행률

## 개발 가이드

### 커밋 규칙 (Conventional Commits)

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
refactor: 코드 리팩토링
test: 테스트 추가
chore: 기타 작업 (빌드, 설정 등)
```

### 브랜치 전략

- `main`: 안정 버전
- `develop`: 개발 중인 버전
- `feature/*`: 각 기능별 브랜치

## 라이센스

MIT License

## 참고 자료

- [FastAPI](https://fastapi.tiangolo.com/)
- [React Query](https://tanstack.com/query/latest)
- [shadcn/ui](https://ui.shadcn.com/)
- [Docker Compose](https://docs.docker.com/compose/)
