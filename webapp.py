from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from src.search.search_engine import SearchEngine

app = Flask(__name__)

# 검색 엔진 초기화
search_engine = SearchEngine()

# 검색 엔진 초기화 및 데이터 직접 로드
print("\n=== 검색 엔진 초기화 ===")
try:
    # CSV 파일에서 직접 데이터 로드
    data = pd.read_csv('data/all_reports_analyzed.csv')
    print(f"CSV 파일 로드 성공: {len(data)}개 항목")
    
    # 인덱스 직접 생성
    search_engine.index_documents(data, text_column='text', title_column='title')
    print("검색 인덱스 생성 완료")
    
except Exception as e:
    print(f"데이터 로드 오류: {e}")
    print("기본 데이터 생성 중...")
    
    # 기본 테스트 데이터 직접 생성
    test_data = {
        'title': ["경제성장 전망", "물가상승 분석", "부동산 정책 효과"],
        'author': ["KDI 경제연구부", "한국은행 조사부", "KDI 부동산연구팀"],
        'date': ["2023-01-01", "2022-06-15", "2021-12-10"],
        'link': ["http://example.com", "http://example.com/bok", "http://example.com/property"],
        'abstract': ["한국 경제성장률 전망 보고서", "인플레이션 영향 분석", "부동산 정책 효과 분석"],
        'keywords': ["경제성장#전망#GDP", "물가#인플레이션#통화정책", "부동산#정책#주택가격"],
        'pdf_link': ["http://example.com/test.pdf", "http://example.com/bok.pdf", "http://example.com/property.pdf"],
        'source': ["KDI", "BOK", "KDI"],
        'text': [
            "경제성장 전망 보고서 내용입니다. 한국 경제는 올해 3% 성장할 것으로 예상됩니다.",
            "물가 상승의 원인과 대응책에 관한 연구. 통화정책 조정이 필요합니다.",
            "부동산 정책의 시장 안정화 효과에 대한 분석. 주택 가격 변동성 연구."
        ]
    }
    # 데이터프레임 생성 및 인덱싱
    test_df = pd.DataFrame(test_data)
    search_engine.index_documents(test_df, text_column='text', title_column='title')
    print("기본 데이터로 검색 엔진 초기화 완료")

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
        print(f"\n=== 검색 시도 ===")
        print(f"검색어: '{query}'")
        
        top_n = int(request.form.get('top_n', 10))
        print(f"결과 수 제한: {top_n}")
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        print(f"날짜 범위: {start_date or '전체'} ~ {end_date or '현재'}")
        
        # 검색 수행
        try:
            results = search_engine.search(query, top_n)
            print(f"검색 결과: {len(results)}개")
            if len(results) > 0:
                print(f"첫 번째 결과: {results[0]['title']}")
            
            # 날짜 필터링
            if start_date or end_date:
                filtered_results = search_engine.filter_by_date(results, start_date, end_date)
                print(f"필터링 후 결과: {len(filtered_results)}개")
                results = filtered_results
            
            return render_template('results.html', results=results, query=query)
        except Exception as e:
            print(f"검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return render_template('results.html', results=[], query=query)
    
    return render_template('search.html')

# 데이터 로드
@app.route('/load_data', methods=['POST'])
def load_data():
    data_path = request.form.get('data_path')
    
    if os.path.exists(data_path):
        search_engine.load_data(data_path)
        return jsonify({'status': 'success', 'message': f'Data loaded from {data_path}'})
    else:
        return jsonify({'status': 'error', 'message': 'File not found'})

# 메인 페이지
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)