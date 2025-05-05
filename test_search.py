import pandas as pd
from src.search.search_engine import SearchEngine

print("=== 검색 엔진 테스트 ===")

# 검색 엔진 초기화
search_engine = SearchEngine()

# CSV 파일 로드
try:
    data = pd.read_csv('data/all_reports_analyzed.csv')
    print(f"CSV 파일 로드 성공: {len(data)}개 항목")

    # 데이터 미리보기
    print("\n=== 데이터 미리보기 ===")
    print(data)

    # 인덱스 생성
    print("\n=== 인덱스 생성 ===")
    search_engine.index_documents(data, text_column='text', title_column='title')
    print("인덱스 생성 완료")

    # 검색 테스트
    print("\n=== 검색 테스트 ===")
    queries = ["경제성장", "물가", "부동산"]
    for query in queries:
        print(f"\n'{query}' 검색 결과:")
        results = search_engine.search(query, top_n=5)
        print(f"결과 수: {len(results)}")
        for i, result in enumerate(results):
            print(f"{i+1}. {result['title']} (점수: {result['score']:.4f})")
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
