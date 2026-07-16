# TravelDiary 발표 전 구현 정리 자료

작성 기준: 2026-07-16 현재 `/Users/betterkim/TravelDiary` 작업본

이 문서는 발표 자료, 기능 명세서, 회고 문서, README 업데이트에 바로 옮길 수 있도록 현재 코드에 구현된 기능과 로직을 정리한 자료다. 기존 `README.md`에는 초기 프로토타입 기준의 "아직 구현되지 않음" 문구가 일부 남아 있으므로, 발표 전 현재 상태 설명은 이 문서를 기준으로 잡는 것이 안전하다.

## 1. 한 줄 소개

TravelDiary는 여행 중 기록된 위치 흐름과 여행 사진을 연결해, 대표 사진과 장소별 메모를 시간순 다이어리로 정리하는 웹 기반 여행 기록 MVP다.

핵심 가치는 다음 한 문장으로 설명할 수 있다.

> 여행이 끝난 뒤 흩어진 사진과 이동 경로를 자동으로 묶어, 하루의 흐름이 보이는 다이어리 초안을 만들어 주고 사용자가 마지막 문장을 직접 고칠 수 있게 한다.

## 2. 현재 구현 요약

| 영역 | 현재 상태 | 설명 |
|---|---:|---|
| 여행 생성 | 구현 | 제목, 날짜, 지역 입력 후 여행 세션 생성 |
| 두 가지 시작 모드 | 구현 | 실시간 기록 시작 / 사진으로 만들기 |
| 지도 화면 | 구현 | Mapbox 기반 지도 초기화, 경로선, 발자국, 사진 마커 표시 |
| 실시간 위치 기록 | 부분 구현 | 브라우저 Geolocation으로 좌표를 로컬 상태와 localStorage에 저장 |
| 현장 사진 | 구현 | 기록 중 촬영/선택한 사진을 현재 위치에 지도 마커로 추가 |
| 사진 업로드 | 구현 | JPEG/PNG 다중 업로드, 서버 저장, EXIF 추출 |
| 사진 메타데이터 추출 | 구현 | 촬영 시간, GPS, 크기 추출 |
| 사진 품질 평가 | 구현 | 선명도, 해상도, 노출, 구도, 채도, 중앙 피사체 힌트 등 점수화 |
| 유사 사진 묶기 | 구현 | average hash와 Hamming distance로 유사 컷 그룹화 |
| 대표 사진 선별 | 구현 | 그룹별 최고 품질 후보를 고르고 최대 3장 선택 |
| 사진 선호 피드백 | 구현 | 좋아요/별로예요를 서버에 저장하고 다음 선별에 반영 |
| 경로 생성 | 구현 | 사진 GPS 우선, 없으면 서버에 저장된 위치 샘플로 경로 생성 |
| 시간순 타임라인 | 구현 | 대표 사진을 촬영 시간순으로 정렬해 다이어리 항목 생성 |
| 장소 매칭 | 구현 | 사진 위치와 정차 지점이 가까우면 장소를 연결, 아니면 이동 중 처리 |
| AI 메모 초안 | 부분 구현 | 실제 외부 AI 호출은 아직 연결 전. 현재는 AI 훅과 담백한 fallback 생성 로직 사용 |
| 메모 수정 | 구현 | 다이어리 카드에서 AI 메모 초안 수정 및 저장 가능 |
| 다이어리 복원 | 구현 | 마지막 서버 다이어리 또는 로컬 저장 여행을 다시 불러옴 |
| 일자별 기록 | 구현 | 달력과 기록 목록으로 저장된 여행 선택 가능 |
| PWA 캐시 | 부분 구현 | service worker로 정적 자산 캐싱, 버전 갱신 적용 |
| 자동 테스트 | 구현 | 백엔드/파이프라인 테스트 22개 통과 |

## 3. 사용자 흐름

### 3.1 실시간 기록 모드

1. 홈 화면에서 여행 제목, 날짜, 지역을 입력한다.
2. `실시간 기록 시작`을 누른다.
3. 앱이 여행을 생성하고 지도 화면으로 이동한다.
4. 위치 권한을 허용하면 현재 위치가 지도에 표시된다.
5. 이동 중 GPS 샘플이 쌓이고 경로선과 발자국이 지도에 표시된다.
6. 기록 중 `현장 사진`을 추가하면 현재 위치에 사진 마커가 찍힌다.
7. `기록 종료` 후 여행 사진을 불러와 다이어리를 생성할 수 있다.

주의: 현재 프런트의 실시간 GPS 샘플은 로컬 상태/localStorage에 저장된다. 백엔드에는 `/api/trips/{trip_id}/locations` 저장 API가 있지만, 프런트에서 이 API로 실시간 샘플을 보내는 연결은 아직 남은 과제다.

### 3.2 사진으로 만들기 모드

1. 홈 화면에서 `사진으로 만들기`를 누른다.
2. 사진 파일을 선택한다.
3. 서버가 사진을 업로드받아 EXIF를 추출한다.
4. 백엔드 파이프라인이 대표 사진과 다이어리를 생성한다.
5. 백엔드 생성이 실패하면 프런트에서 사진 EXIF와 로컬 GPS 샘플을 이용해 fallback 다이어리를 만든다.
6. 결과는 시간순 다이어리 화면에 표시된다.

### 3.3 다이어리 확인 및 수정

1. 다이어리 화면에는 시간, 장소, 사진 수, 기록 시간, 대표 사진, 메모 초안이 표시된다.
2. 각 카드의 `지도에서 보기`를 누르면 지도 화면으로 이동하고 해당 위치 중심으로 지도를 이동한다.
3. `AI 메모 초안` 옆 `수정`을 누르면 textarea가 열린다.
4. 사용자가 메모를 고치고 `저장`하면 로컬 기록에 반영된다.
5. 서버 다이어리 ID가 있는 경우 서버의 다이어리 JSON도 함께 수정된다.

## 4. 프런트엔드 구현 상세

주요 파일:

- `index.html`: 화면 구조, 홈/지도/다이어리 섹션, 파일 입력
- `styles.css`: 모바일 중심 UI, 타임라인/지도/캘린더/메모 편집 스타일
- `app.js`: 상태 관리, 지도, 사진 처리, 다이어리 렌더링, API 호출
- `service-worker.js`: 정적 자산 캐시
- `config.js`, `config.local.js`: Mapbox/API 설정

### 4.1 상태 관리

`app.js`는 별도 프레임워크 없이 하나의 `state` 객체로 화면과 여행 상태를 관리한다.

주요 상태:

- `screen`: 현재 화면(create/map/diary)
- `mapState`: 지도 기록 상태(before/recording/after)
- `tripId`: 서버 여행 ID
- `activeTrip`, `activeTripId`: 현재 작업 중인 로컬 여행
- `savedTrips`: localStorage에서 복원되는 여행 목록
- `generatedDiary`: 현재 보여줄 다이어리 엔트리
- `locationSamples`: 현재 세션의 GPS 샘플
- `acceptedPhotoIds`, `rejectedPhotoIds`: 사진 선호 피드백

로컬 저장 키:

- `travel-diary.trips.v1`: 저장된 여행 목록
- `travel-diary:create-form`: 홈 입력값 임시 저장
- `travel-diary:last-trip-id`: 마지막 서버 여행 ID

### 4.2 지도 로직

구현 함수:

- `initMapIfNeeded()`: Mapbox 지도 초기화
- `ensureRouteLayer()`: 경로선 레이어 준비
- `setRouteLine(coordinates)`: 경로 GeoJSON 갱신
- `addFootprint(lngLat)`: 발자국 마커 추가
- `addLivePhotoMarker(lngLat, dataUrl)`: 현장 사진 마커 추가
- `renderTripOnMap(trip)`: 저장된 여행의 경로, 발자국, 사진 위치 복원
- `centerMapOn(lngLat, zoom)`: 특정 위치로 지도 이동

지도 표시 우선순위:

1. 실시간 GPS 샘플이 있으면 샘플로 경로선을 그린다.
2. GPS 샘플이 없고 저장된 사진 좌표가 있으면 사진 좌표로 경로를 그린다.
3. 사진 좌표도 없고 다이어리 엔트리 위치가 있으면 다이어리 위치로 경로와 발자국을 복원한다.

### 4.3 실시간 위치 기록 로직

구현 함수:

- `startRecording()`: 위치 추적 시작
- `handlePosition(position)`: 새 좌표 수신 처리
- `handlePositionError(error)`: 위치 권한/실패 처리
- `endRecording()`: 기록 종료 후 사진 불러오기 단계로 전환
- `stopTracking()`: watchPosition과 타이머 정리

동작:

- `navigator.geolocation.watchPosition` 사용
- 좌표가 들어올 때마다 `state.locationSamples`와 `activeTrip.recording.samples`에 저장
- 지도 경로선 즉시 갱신
- 이전 발자국 이후 15초 이상 지났고 1m 이상 움직였으면 발자국 마커 추가
- 첫 위치를 받으면 Mapbox reverse geocoding으로 여행 제목 자동 제안

### 4.4 사진 처리 로직

프런트 fallback 처리:

- `parsePhotoFile(file)`: 파일 ArrayBuffer와 미리보기 dataURL 생성
- `parseExifBuffer(arrayBuffer)`: JPEG EXIF에서 촬영 시간과 GPS 추출
- `estimatePhotoLocation(photo)`: 사진 GPS가 없으면 기록된 GPS 샘플의 시간 전후를 이용해 위치 보정
- `buildClusters(photos, allowCrossDate)`: 같은 날짜, 가까운 위치, 짧은 시간 간격의 사진을 위치별 묶음으로 정리
- `resolvePlaceName(lng, lat, fallbackLabel)`: Mapbox reverse geocoding으로 장소명 조회
- `generateDiaryFromFiles(files)`: 프런트 fallback 다이어리 생성

클러스터 기준:

- 기본 반경: 50m
- 같은 묶음으로 볼 최대 사진 간격: 10분
- 같은 지점 판단: anchor center와 현재 center 모두 50m 이내
- 날짜가 여러 개면 사용자 확인 후 같은 여행으로 묶을 수 있음

### 4.5 다이어리 렌더링 및 메모 수정

구현 함수:

- `renderTimeline(entries)`: 다이어리 카드 렌더링
- `saveDiaryNote(entryIndex, note, entries)`: 메모 저장 진입점
- `persistDiaryNoteLocally(entryIndex, note, entries)`: 로컬 상태와 localStorage 반영
- `persistDiaryNoteToApi(entryIndex, note)`: 서버 PATCH API 호출
- `escapeHtml(value)`: 렌더링 시 HTML injection 방지

UI 요소:

- 카드별 `지도에서 보기`
- 대표 사진 최대 3장
- 사진별 좋아요/별로예요 피드백
- `AI 메모 초안` 라벨
- `수정`, `저장`, `취소` 버튼
- 300자 제한
- 빈 메모 저장 방지

## 5. 백엔드 구현 상세

주요 파일:

- `backend/app.py`: FastAPI 엔드포인트
- `backend/models.py`: Pydantic 데이터 계약
- `backend/storage.py`: SQLite 저장소
- `backend/pipeline.py`: 전체 처리 파이프라인
- `backend/services/location.py`: GPS 정리
- `backend/services/route.py`: 경로/정차 지점 계산
- `backend/services/exif.py`: EXIF 추출
- `backend/services/quality.py`: 사진 품질 평가
- `backend/services/dedupe.py`: 유사 사진 그룹화
- `backend/services/selector.py`: 대표 사진 선별
- `backend/services/timeline.py`: 경로와 사진 매칭
- `backend/services/diary.py`: 제목/메모 생성

### 5.1 API 목록

| 메서드 | 경로 | 용도 |
|---|---|---|
| POST | `/api/trips` | 여행 생성 |
| POST | `/api/trips/{trip_id}/locations` | GPS 좌표 배치 저장 |
| POST | `/api/trips/{trip_id}/photos` | 사진 업로드 및 EXIF 저장 |
| GET | `/api/trips/{trip_id}/photos` | 저장된 사진 메타데이터 조회 |
| POST | `/api/trips/{trip_id}/generate` | 사진/경로 기반 다이어리 생성 |
| POST | `/api/trips/{trip_id}/photo-feedback` | 대표 사진 선호 피드백 저장 |
| GET | `/api/trips/{trip_id}/diary` | 저장된 다이어리 조회 |
| PATCH | `/api/trips/{trip_id}/diary/notes/{entry_index}` | 다이어리 메모 수정 |
| GET | `/api/trips/latest` | 마지막 여행 ID 조회 |

정적 제공:

- `/uploads`: 업로드된 사진 파일
- `/outputs`: 생성 산출물
- `/`: 프런트엔드 정적 파일

### 5.2 데이터 모델

핵심 모델:

- `TripCreate`: title, start_date, region
- `LocationPoint`: lat, lng, time, accuracy_m
- `Route`: distance_m, duration_sec, stops
- `Stop`: lat, lng, arrived_at, left_at, place
- `Photo`: photo_id, filename, taken_at, lat, lng, width, height, 품질 점수들, group_id
- `SelectedPhoto`: photo_id, photo_url, reason
- `PhotoFeedback`: accepted_photo_ids, rejected_photo_ids, notes
- `DiaryNoteUpdate`: note
- `TimelineEntry`: time, place, note, photo_url, lat, lng
- `Diary`: trip_id, title, route, selected_photos, timeline

### 5.3 저장소 구조

SQLite DB: `data/travel_diary.sqlite3`

테이블:

- `trips`: trip_id, meta_json, diary_json, photo_feedback_json
- `locations`: trip_id별 GPS 좌표
- `photos`: trip_id별 사진 메타데이터 JSON

저장 방식:

- Pydantic 모델을 JSON으로 dump해 저장
- 다이어리는 `trips.diary_json`에 통째로 저장
- 사진 피드백은 `photo_feedback_json`에 저장

### 5.4 전체 파이프라인

`backend/pipeline.py`의 `generate(trip_id)` 흐름:

1. 저장된 사진 메타데이터 조회
2. 사진 EXIF GPS/촬영 시간으로 먼저 경로 생성 시도
3. 사진 기반 경로가 불가능하면 서버에 저장된 GPS 좌표를 정리해 경로 생성
4. 각 사진 품질 평가
5. 유사 사진 그룹화
6. 사용자 피드백 기반 선호 프로필 구성
7. 대표 사진 최대 3장 선별
8. 대표 사진과 경로를 매칭해 시간순 타임라인 생성
9. 다이어리 메모 초안 채우기
10. 지역/장소 기반 제목 생성
11. 결과를 DB에 저장하고 반환

## 6. 알고리즘 상세

### 6.1 GPS 정리

파일: `backend/services/location.py`

처리 기준:

- `accuracy_m > 100m`이면 제외
- 직전 좌표 대비 속도가 약 300km/h 이상이면 순간이동으로 보고 제외
- 직전 좌표와 2m 미만 차이면 중복으로 보고 제외
- 결과는 시간순으로 정렬

### 6.2 경로 및 정차 지점 계산

파일: `backend/services/route.py`

처리 기준:

- 좌표를 시간순 정렬
- 연속 좌표 사이 Haversine distance로 총 이동거리 계산
- 같은 장소 반경: 30m
- 같은 장소에 3분 이상 머물면 정차 지점으로 기록
- 사진 GPS/시간이 2장 이상 있으면 사진 위치로 경로를 우선 생성

### 6.3 EXIF 추출

파일: `backend/services/exif.py`

추출 항목:

- 촬영 시간: DateTimeOriginal, DateTimeDigitized, DateTime
- GPS: 위도/경도 DMS + N/S/E/W 방향
- 이미지 크기: EXIF orientation 보정 후 width/height

실패 처리:

- 이미지가 아니거나 EXIF가 없어도 예외로 파이프라인이 멈추지 않음
- 파일명과 photo_id만 가진 Photo로 통과

### 6.4 사진 품질 평가

파일: `backend/services/quality.py`

점수 항목:

- 선명도: Laplacian variance
- 해상도: megapixels + short edge
- 노출: 평균 밝기 + 암부/하이라이트 clipping
- 구도: 중앙부와 전체 밝기 차이
- 화면 균형: 좌우/상하 밝기 균형
- 채도: 평균 saturation의 적정성
- 중앙 피사체 힌트: 중앙부 디테일과 테두리 디테일 비교
- 역광 추정: 테두리는 밝고 중앙은 어두운 경우 감점

최종 가중치:

- 선명도 40%
- 해상도 20%
- 노출 15%
- 구도 15%
- 화면 균형 5%
- 채도 3%
- 중앙 피사체 힌트 2%
- 역광은 별도 감점

하드 컷:

- 심한 흔들림/초점 실패
- 너무 어두움
- 노출 과다
- 해상도 부족
- 역광으로 피사체가 어두움

### 6.5 유사 사진 그룹화

파일: `backend/services/dedupe.py`

처리 방식:

- 이미지를 흑백 8x8로 축소
- 평균 밝기 기준으로 64비트 average hash 생성
- Hamming distance가 10 이하이면 같은 그룹으로 묶음
- 유사 그룹별로 대표 후보 1장을 남기는 데 사용

### 6.6 대표 사진 선별

파일: `backend/services/selector.py`

처리 방식:

1. `group_id` 기준으로 사진을 묶음
2. 그룹 안에서 rejected가 아닌 사진을 우선 후보로 사용
3. 그룹 전체가 rejected이면 빈 결과를 피하기 위해 그중 최고 점수 사진을 후보로 둠
4. quality, composition, face_hint, resolution 순으로 정렬
5. 최대 3장을 `SelectedPhoto`로 반환
6. 각 대표 사진에 선택 이유를 붙임

선택 이유 예시:

- `유사 3장 중 대표 (품질 0.82 / 구도 양호, 노출 안정)`
- `단독 사진 (품질 0.74 / 중앙 피사체)`

사용자 피드백 반영:

- 좋아요/별로예요 사진의 품질/구도/중앙 피사체 점수 평균 차이를 계산
- 다음 대표 사진 선별 시 선호가 드러난 지표에 boost 적용

### 6.7 타임라인 생성

파일: `backend/services/timeline.py`

처리 방식:

- 대표 사진을 촬영 시간순으로 정렬
- 사진 GPS가 정차 지점 200m 이내면 해당 정차 지점 장소로 매칭
- 가까운 정차 지점이 없으면 `이동 중`으로 처리
- 촬영 시간이 없으면 정차 지점 도착 시각 또는 현재 시각 fallback
- 각 TimelineEntry는 time, place, note, photo_url, lat, lng를 가진다

### 6.8 AI 메모 초안 설계

파일: `backend/services/diary.py`

현재 상태:

- 실제 외부 AI SDK 호출은 아직 연결 전
- `AI_API_KEY` 설정을 확인하는 훅은 있음
- 현재는 fallback 로직으로 메모 초안을 생성

짜치지 않게 설계한 기준:

- 감정 과장 금지
- 사진에 없는 사건/사람/감정 만들지 않기
- `소중한 순간`, `행복한 하루`, `잊지 못할` 같은 상투어 피하기
- 전체 주소가 길면 첫 장소명만 사용
- 시간대 + 장소 + 동선상 의미 중심으로 작성
- 사용자가 고쳐 쓰기 쉬운 관찰형 문장으로 제한

현재 fallback 문장 방향:

- `오후 성수동 카페거리에서 남긴 기록. 이 위치가 오늘 동선의 한 지점으로 선명하게 잡혔어요.`
- `성수동 카페거리에 머문 흔적을 오후 기록으로 묶었어요. 사진과 위치가 같은 흐름 안에 있어요.`
- `오후의 성수동 카페거리 기록. 이동 중 지나친 곳이 아니라 잠시 멈춘 지점으로 정리했어요.`

## 7. 발표에서 강조할 수 있는 구현 포인트

### 7.1 단순 사진첩이 아니라 "경로 기반 다이어리"

사진만 나열하는 것이 아니라, GPS와 촬영 시간을 기준으로 하루의 이동 흐름을 재구성한다.

발표 문장:

> 사진첩은 결과만 보여주지만, TravelDiary는 내가 어떤 순서로 움직였는지까지 복원해서 하루를 다이어리로 만든다.

### 7.2 대표 사진 자동 선별

수십 장 중복 사진을 모두 보여주지 않고, 유사 사진을 묶은 뒤 품질이 좋은 사진을 대표로 고른다.

발표 문장:

> 사용자가 직접 고르기 귀찮은 중복 컷을 먼저 줄이고, 품질과 구도를 기준으로 대표 사진만 남긴다.

### 7.3 AI 메모는 최종 글이 아니라 초안

AI가 모든 것을 결정하는 구조가 아니라, 사용자가 고쳐 쓸 수 있는 초안을 만든다.

발표 문장:

> AI 메모는 감성 문장을 완성해 주는 기능이 아니라, 사용자가 기억을 꺼내기 쉽게 첫 문장을 놓아 주는 기능이다.

### 7.4 사용자 피드백이 다음 선별에 반영됨

좋아요/별로예요를 단순 반응으로 끝내지 않고 다음 사진 선별 preference profile로 사용한다.

발표 문장:

> 대표 사진이 마음에 들지 않으면 피드백을 줄 수 있고, 다음 생성에서는 그 선택 기준이 반영된다.

### 7.5 실패해도 멈추지 않는 fallback 구조

서버 생성이 실패하면 프런트가 EXIF와 로컬 GPS 기록으로 fallback 다이어리를 만든다.

발표 문장:

> API나 AI가 완벽하지 않아도 전체 사용자 흐름이 끊기지 않게 fallback을 먼저 설계했다.

## 8. 데모 시나리오

### 시나리오 A: 사진으로 다이어리 만들기

1. 홈에서 날짜/지역 입력
2. `사진으로 만들기` 클릭
3. 위치/촬영 시간이 있는 사진 선택
4. 업로드 진행률 확인
5. 다이어리 화면에서 시간순 카드 확인
6. 대표 사진과 사진 수 확인
7. `지도에서 보기` 클릭
8. 메모 `수정` 클릭 후 문장 고치기
9. `저장` 후 문장 반영 확인

### 시나리오 B: 실시간 기록

1. `실시간 기록 시작` 클릭
2. 위치 권한 허용
3. 지도에서 현재 위치와 발자국 확인
4. `현장 사진`으로 지도 마커 추가
5. `기록 종료`
6. 여행 사진 불러오기
7. 기록된 GPS와 사진 촬영 시간을 연결해 다이어리 생성

### 시나리오 C: 선호 피드백

1. 다이어리 대표 사진에서 좋아요/별로예요 클릭
2. 서버에 피드백 저장
3. 다음 generate에서 preference profile이 반영되는 구조 설명

## 9. 테스트 및 검증 자료

테스트 파일:

- `tests/test_location.py`: 좌표 정렬/정리
- `tests/test_route.py`: 거리/정차 지점/사진 기반 경로
- `tests/test_exif.py`: EXIF 추출
- `tests/test_quality.py`: 사진 품질 평가
- `tests/test_dedupe.py`: 유사 사진 그룹화
- `tests/test_selector.py`: 대표 사진 선택
- `tests/test_timeline.py`: 시간순 타임라인
- `tests/test_diary.py`: 메모 생성/상투어 회피
- `tests/test_pipeline.py`: API 전체 흐름, 사진 GPS 우선 경로, 메모 수정 저장
- `tests/test_photo_curation.py`: 사진 정리 파이프라인 보강 테스트

최근 확인 결과:

- `node --check app.js`: 통과
- `npm run build`: 통과
- `.venv/bin/python -m pytest`: 22 passed

브라우저 확인:

- 새 버전 `app.js?v=20260716a` 로드 확인
- 다이어리 카드별 메모 수정 UI 렌더링 확인
- 서비스워커 캐시 버전 `travel-diary-cache-v2` 반영

## 10. 산출물로 활용 가능한 기존 자료

문서/발표 자료 후보:

- `README.md`: 프로젝트 목표, 팀 분담, API 초안, 보안/개인정보 원칙
- `docs/TEAM_GUIDE.md`: 팀 개발 가이드
- `outputs/TravelDiary_Day2_Project_Status_Brief.docx`: 기존 상태 보고서
- `outputs/day2_doc_render/TravelDiary_Day2_Project_Status_Brief.pdf`: 렌더링된 PDF
- `outputs/TravelDiary_MVP_Architecture.png`: 아키텍처 이미지
- `backend/fixtures/sample_diary.json`: 다이어리 응답 예시
- `prompts/curator.txt`: AI 다이어리 큐레이터 프롬프트 초안

발표 자료에 바로 넣을 수 있는 도식:

```text
여행 생성
  -> 실시간 GPS 기록 또는 사진 업로드
  -> EXIF 촬영시간/GPS 추출
  -> 사진 품질 평가
  -> 유사 사진 그룹화
  -> 대표 사진 최대 3장 선별
  -> 경로와 사진 매칭
  -> 시간순 다이어리 생성
  -> AI 메모 초안
  -> 사용자 수정/저장
```

## 11. 현재 한계와 발표 시 표현법

| 항목 | 현재 한계 | 발표 표현 |
|---|---|---|
| 외부 AI 호출 | 실제 AI SDK 호출은 아직 미연결 | AI 메모 생성 훅과 fallback 로직을 먼저 구현했고, API 키 연동 시 확장 가능 |
| 실시간 GPS 서버 저장 | 프런트가 위치 API로 샘플을 보내는 연결은 아직 없음 | 현재는 로컬 기록 중심이며, 백엔드 저장 API는 준비됨 |
| 장소명 품질 | Mapbox reverse geocoding 결과에 의존 | 위치 기반 장소명은 외부 지도 API 품질에 영향받음 |
| 사진 GPS 없는 경우 | 실시간 기록 샘플이 없으면 위치 추정 불가 | EXIF GPS 또는 기록된 GPS 중 하나가 있어야 위치별 다이어리 정확도가 올라감 |
| 실제 대량 사진 | MAX_PHOTOS 30장 기준 MVP | 대량 처리보다 10~30장 MVP 흐름 완성을 우선함 |
| 개인정보 | 사진/GPS는 민감정보 | API 키는 서버에 두고, 사진과 위치 데이터는 민감정보로 취급 |

발표에서 피해야 할 과장:

- "AI가 완전히 자동으로 감성 다이어리를 작성한다"는 표현은 부정확하다.
- "실시간 GPS가 서버까지 완전히 저장된다"는 표현은 현재 프런트 기준으로 부정확하다.
- "장소명을 완벽히 인식한다"는 표현은 지도 API 의존 때문에 부정확하다.

발표에서 안전한 표현:

- "현재는 AI 메모 초안 생성 구조와 수정/저장 흐름까지 구현했다."
- "외부 AI 호출은 훅을 열어 두었고, fallback 문장 생성으로 데모가 끊기지 않게 했다."
- "프런트 로컬 기록과 백엔드 파이프라인을 모두 갖췄고, 다음 단계는 실시간 GPS 서버 동기화다."

## 12. 파일별 책임 정리

| 파일 | 발표용 설명 |
|---|---|
| `index.html` | 앱의 세 화면 구조와 파일 입력을 정의 |
| `styles.css` | 모바일 앱 형태의 UI와 타임라인/메모 편집 스타일 |
| `app.js` | 프런트 상태 관리, 지도, 사진 처리, API 연동, 다이어리 UI |
| `service-worker.js` | 정적 파일 캐시와 새 버전 반영 |
| `backend/app.py` | FastAPI 엔드포인트 |
| `backend/models.py` | 팀이 공유하는 데이터 계약 |
| `backend/storage.py` | SQLite 저장/조회 |
| `backend/pipeline.py` | 전체 다이어리 생성 파이프라인 |
| `backend/services/location.py` | GPS 이상치 제거 |
| `backend/services/route.py` | 거리와 정차 지점 계산 |
| `backend/services/exif.py` | 사진 촬영시간/GPS 추출 |
| `backend/services/quality.py` | 사진 품질 점수 계산 |
| `backend/services/dedupe.py` | 유사 사진 그룹화 |
| `backend/services/selector.py` | 대표 사진 선택 |
| `backend/services/timeline.py` | 대표 사진과 경로 매칭 |
| `backend/services/diary.py` | 제목과 메모 초안 생성 |
| `tests/` | 각 모듈과 전체 흐름 검증 |

## 13. 발표 슬라이드 구성안

1. 문제 정의: 여행 사진은 많지만 기록 정리는 미뤄진다
2. 서비스 한 줄 설명: 경로와 사진을 묶어 시간순 다이어리로 만든다
3. 사용자 흐름: 실시간 기록 / 사진으로 만들기
4. 시스템 구조: 프런트, FastAPI, SQLite, Mapbox, 사진 파이프라인
5. 사진 처리 로직: EXIF, 품질 평가, 유사 사진, 대표 사진
6. 경로 처리 로직: GPS 정리, 거리 계산, 정차 지점
7. 다이어리 생성: 시간순 타임라인, 장소 매칭, 메모 초안
8. 사용자 수정: AI 초안을 직접 고쳐 저장
9. 데모: 사진 업로드부터 지도 보기/메모 수정까지
10. 현재 한계와 다음 단계: 실제 AI 호출, GPS 서버 동기화, 장소명 고도화

## 14. 다음 개발 우선순위

1. 프런트 실시간 GPS 샘플을 `/api/trips/{trip_id}/locations`로 주기적 전송
2. 외부 AI SDK 연결: `backend/services/diary.py`의 `_try_ai_notes`
3. AI 프롬프트를 `prompts/curator.txt` 기준으로 서버 호출에 연결
4. 다이어리 메모 수정 후 서버 응답을 프런트 상태에 더 강하게 동기화
5. 사진 업로드 후 서버 대표 사진 결과와 프런트 fallback 결과의 표시 형식 통일
6. Mapbox 토큰 누락/지도 로드 실패 시 안내 화면 개선
7. README의 구현 상태 섹션을 현재 기준으로 업데이트
8. 실제 샘플 사진/샘플 GPS로 데모 데이터 세트 구성

