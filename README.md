# 사진 포맷 변환기

Windows용 로컬 사진 포맷 변환 프로그램입니다. 파일은 서버로 업로드하지 않고 PC 안에서 변환합니다.

## 지원 포맷

입력:

- iPhone 사진: HEIC, HEIF, HIF, JPG, PNG
- Android 사진: JPG, PNG, WebP, HEIC, HEIF, AVIF, DNG
- 일반 이미지: BMP, GIF, TIFF, ICO, PDF, TGA, PPM 등
- RAW 계열: DNG, RAW, NEF, CR2, CR3, ARW, RW2, ORF, RAF

출력:

- PNG, JPEG, WebP, AVIF, HEIC, HEIF, BMP, TIFF, GIF, ICO, PDF, TGA, PPM

## 개발 실행

```bat
python -m pip install -r requirements.txt
python photo_converter.py
```

## Windows 배포 빌드

```bat
pyinstaller --noconfirm --clean --windowed --onedir --name PhotoFormatConverter photo_converter.py
```

빌드 결과는 `dist/PhotoFormatConverter/PhotoFormatConverter.exe`에 생성됩니다.
