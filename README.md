# TrackMate MCP

택배 추적부터 문제 해결까지, AI가 알아서 챙겨주는 스마트 배송 비서

## 특징

- **자연어 운송장 입력**: 카톡 문자 그대로 붙여넣기만 하면 운송장 번호 자동 추출
- **배송 용어 번역**: "SM입고", "간선상차" 같은 어려운 용어를 쉽게 설명
- **문제 진단**: 배송 지연/정체 시 원인 분석 및 해결책 제안
- **문의 템플릿**: 택배사/판매자 문의용 템플릿 자동 생성

## Tools

| Tool | 설명 |
|------|------|
| `parse_tracking` | 자연어/문자에서 운송장 번호 추출 |
| `track_package` | 배송 추적 + 상태 번역 |
| `my_packages` | 여러 택배 한번에 조회 |
| `predict_arrival` | 도착 시간 예측 |
| `diagnose_problem` | 배송 문제 진단 + 해결책 |
| `draft_inquiry` | 문의 템플릿 생성 |

## 설치

```bash
# 의존성 설치
pip install -e .

# 또는
pip install mcp[cli] fastmcp httpx pydantic python-dotenv
```

## 설정

1. Sweet Tracker API 키 발급: https://tracking.sweettracker.co.kr
2. `.env` 파일 생성:

```env
SWEET_TRACKER_API_KEY=your_api_key_here
```

## 실행

```bash
# 로컬 실행
python -m src.server

# 또는
trackmate
```

## 사용 예시

### 카톡 문자에서 추적
```
👤 "카톡에 온 택배 번호 추적해줘"
🤖 "문자 내용을 보내주세요"
👤 "[CJ대한통운] 운송장번호 640123456789"
🤖 "CJ대한통운 배송 현황
    현재: 기사님이 물건 받았어요! (SM입고)
    예상 도착: 오늘 오후 3-5시"
```

### 문제 진단
```
👤 "택배가 3일째 안 움직여"
🤖 "부산 허브에서 3일째 정체 중
    원인: 물량 폭주(60%) / 분류 누락(30%)
    추천: 택배사 문의 (1588-1255)"
```

## 지원 택배사

- CJ대한통운
- 롯데택배
- 한진택배
- 우체국택배
- 로젠택배
- 일양로지스
- 경동택배
- CU편의점택배
- 대신택배
- 외 다수

## 라이선스

MIT
