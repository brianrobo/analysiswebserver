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

### 개발 환경 실행

```bash
# 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 접속
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 로컬 개발

**백엔드:**
```bash
cd backend
poetry install
poetry run uvicorn api.main:app --reload
```

**프론트엔드:**
```bash
cd frontend
npm install
npm run dev
```

## 구현 계획

상세한 구현 계획은 [여기](./.claude/plans/serialized-petting-falcon.md)를 참조하세요.

### 구현 단계

- [x] Phase 0: GitHub 레포지토리 초기화
- [ ] Phase 1: FastAPI 백엔드 기반 구축
- [ ] Phase 2: PyQt 분석 로직 통합
- [ ] Phase 3: REST API 및 WebSocket 개발
- [ ] Phase 4: React SPA 프론트엔드 개발
- [ ] Phase 5: Docker 환경 구성
- [ ] Phase 6: 통합 테스트 및 검증

## API 엔드포인트

### 인증
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/register` - 회원가입
- `GET /api/v1/auth/me` - 현재 사용자 정보

### 분석
- `POST /api/v1/analysis/upload` - 파일 업로드
- `POST /api/v1/analysis/start` - 분석 시작
- `GET /api/v1/analysis/{job_id}/status` - 상태 조회
- `GET /api/v1/analysis/{job_id}/result` - 결과 다운로드
- `GET /api/v1/analysis/history` - 이력 조회

### WebSocket
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
