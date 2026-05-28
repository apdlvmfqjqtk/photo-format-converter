# 초고속 로컬 사진 포맷 일괄 변환기 (Photo Format Converter)

본 프로젝트는 개인 정보 보호와 처리 속도를 극대화한 **100% 로컬 구동 사진 포맷 변환기**입니다. 모든 변환 및 보정 작업은 사용자의 PC 내부에서만 수행되며, 어떠한 이미지 파일도 외부 서버로 업로드되지 않습니다.

사용자의 필요에 따라 **Windows 데스크톱 애플리케이션(Python/Tkinter)**과 **설치가 필요 없는 웹 앱(HTML/JS/CSS)** 두 가지 방식을 모두 지원합니다.

---

## 🌟 주요 특징 및 지원 기능

### 1. 데스크톱 프로그램 버전 (`photo_converter.py`)
- **디자인 개편**: 투박한 기본 OS 스타일을 탈피하고, `clam` 테마 기반의 모던 플랫 인디고(Indigo) 테마로 리뉴얼되었습니다.
- **상세 변환 통계**: 변환 후 파일명, 새 용량, 원본 대비 용량 절감비율(%)이 테이블에 명확하게 노출됩니다.
- **이미지 보정 및 변형**:
  - **크기 조절 (5대 모드)**: 원본 크기 유지, 비율 축소(%), 고정 너비(px), 고정 높이(px), 가로/세로 최대 제한(Fit).
  - **회전/반전**: 90도 회전(CW/CCW), 180도 회전, 상하/좌우 대칭 반전.
  - **색상 필터**: 흑백(Grayscale) 필터 원클릭 처리.
- **파일명 커스터마이징**: 변환 대상 파일에 커스텀 접두사(Prefix) 및 접미사(Suffix) 추가 기능.

### 2. 브라우저용 웹앱 버전 (`index.html`)
- **다크 테마 & 반응형 UI**: 네온 테두리 글로우 효과가 가미된 드롭존과 투명 유리 효과(Glassmorphism) 제어판 레이아웃.
- **HEIC/HEIF 브라우저 디코딩**: iOS 디바이스의 `.heic`, `.heif`, `.hif`, `.hifc` 확장자 파일을 드래그하면, 웹 브라우저가 라이브러리(`heic2any`)를 로컬로 적재하여 즉시 화면상에 디코딩 및 미리보기를 완성합니다.
- **Ctrl+V 클립보드 붙여넣기 연동**: 웹브라우저 창 안에서 붙여넣기하면 클립보드의 캡처 이미지나 파일이 변환 대기열에 즉시 추가됩니다.
- **인터랙티브 세부 보정 슬라이더**: 밝기(Brightness), 대비(Contrast), 채도(Saturation), 블러(Blur) 슬라이더 게이지가 탑재되어 이미지 품질을 세밀하게 보정합니다.
- **자동 다운로드**: 변환 완료 즉시 로컬 PC의 다운로드 폴더로 자동 저장되는 토글 스위치 지원.
- **일괄 다운로드 (ZIP)**: 변환 성공한 모든 이미지를 원클릭으로 합쳐 하나의 압축 파일(`.zip`)로 생성하여 내려받습니다.
- **미리보기 라이트박스 모달**: 썸네일 클릭 시 상세 변환 정보(원본 크기 ➡ 최종 크기)와 큰 화면으로 변환 결과를 점검할 수 있습니다.

---

## 🔄 OS별 파일 포맷 상호 변환 규격 안내

| OS 구분 | 대표 이미지 규격 | 입력 지원 여부 (웹/데스크톱) | 출력 지원 여부 (웹/데스크톱) |
| :--- | :--- | :--- | :--- |
| **iOS (Apple)** | HEIC, HEIF, HIF, HIFC, JPG, PNG | 웹 & 데스크톱 모두 지원 (로컬 디코딩) | **데스크톱 전용 지원** (HEIC/HEIF/HIF 출력) |
| **Android (Google)** | JPG, PNG, WebP, AVIF, DNG | 웹 & 데스크톱 모두 지원 | 웹 & 데스크톱 모두 지원 (AVIF, WebP 등) |
| **Windows / Web** | PNG, JPG, WebP, BMP, TIFF, ICO, GIF | 웹 & 데스크톱 모두 지원 | 웹 & 데스크톱 모두 지원 (BMP/ICO 커스텀 인코더 탑재) |
| **DSLR / RAW** | DNG, NEF, CR2, CR3, ARW, RW2, RAF | 데스크톱 지원 (`rawpy` 라이브러리 필요) | - |

> [!WARNING]
> **HEIC/HEIF 출력 제약 안내**
> - HEIC/HEIF 포맷 인코딩에는 HEVC 비디오 코덱 라이선스가 수반됩니다. 웹버전 브라우저 내에서는 인코더 라이선스 제약으로 HEIC/HEIF의 **읽기 및 타 포맷 변환**만 가능하며, 타 포맷에서 **HEIC로의 변환 출력**은 데스크톱 프로그램 버전에서만 가능합니다.

---

## 🚀 사용법 및 개발 가이드

### 1. 웹 버전 실행
다운로드 또는 클론한 디렉토리의 `index.html` 파일을 브라우저로 열기만 하면 설치 없이 실행됩니다.

### 2. 데스크톱 앱 로컬 실행 (Python)
의존성 라이브러리를 설치한 뒤 실행합니다.
```bat
python -m pip install -r requirements.txt
python photo_converter.py
```

### 3. Windows 배포용 빌드
PyInstaller를 통해 무설치 단일 폴더 릴리즈 버전을 생성할 수 있습니다.
```bat
pyinstaller --noconfirm --clean --windowed --onedir --name PhotoFormatConverter photo_converter.py
```
빌드가 완료되면 `dist/PhotoFormatConverter/` 아래에 실행 파일(`PhotoFormatConverter.exe`)이 동적 라이브러리들과 함께 패키징됩니다.
이후 `dist/PhotoFormatConverter` 폴더를 ZIP 파일로 압축하여 배포합니다.

---

## 🛠 사용된 핵심 오픈소스 라이브러리
- **데스크톱**: [Pillow](https://python-pillow.org/), [pillow-heif](https://github.com/bigcat88/pillow_heif), [rawpy](https://github.com/letmaik/rawpy)
- **웹 브라우저**: [JSZip](https://stuk.github.io/jszip/), [heic2any](https://alexcorvi.github.io/heic2any/)
