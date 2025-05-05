# 국책연구기관 자료 크롤링 및 분석 시스템

KDI와 한국은행(BOK) 등 국책연구기관의 연구보고서를 크롤링하고 분석하는 시스템입니다.

## 기능

- 국책연구기관 웹사이트 크롤링
- PDF 파일 다운로드 및 텍스트 추출
- 텍스트 분석 및 키워드 추출
- 토픽 모델링
- 검색 엔진 구축
- 정책 분석 보고서 생성

## 설치 방법

1. 필요 패키지 설치:
```bash
pip install -r requirements.txt
```

2. Java JDK 설치 (KoNLPy 요구사항)

## 사용 방법

### 전체 시스템 실행:
```bash
python main.py --run_all
```

### 특정 기능만 실행:
```bash
# KDI 자료만 크롤링
python main.py --crawl_kdi --start_page 1 --end_page 10

# PDF 처리
python main.py --process_all

# 텍스트 분석
python main.py --analyze --top_keywords 30 --num_topics 8

# 검색 인덱스 구축
python main.py --build_index

# 보고서 생성
python main.py --generate_reports
```

### 웹 인터페이스 실행:
```bash
python webapp.py
```
웹 브라우저에서 http://localhost:5000 접속

## 주의사항

- 각 기관 웹사이트의 이용약관 및 robots.txt 준수
- 크롤링 속도 제한으로 서버 부하 방지
- 텍스트 추출 품질은 PDF 형식에 따라 달라질 수 있음