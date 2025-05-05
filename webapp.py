from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from src.search.search_engine import SearchEngine

app = Flask(__name__)

# 검색 엔진 초기화
search_engine = SearchEngine()

# 데이터 로드
@app.route('/load_data', methods=['POST'])
def load_data():
    data_path = request.form.get('data_path')
    
    if os.path.exists(data_path):
        search_engine.load_data(data_path)
        return jsonify({'status': 'success', 'message': f'Data loaded from {data_path}'})
    else:
        return jsonify({'status': 'error', 'message': 'File not found'})

# 검색 기능
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query', '')
        top_n = int(request.form.get('top_n', 10))
        
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # 검색 수행
        results = search_engine.search(query, top_n)
        
        # 날짜 필터링
        if start_date or end_date:
            results = search_engine.filter_by_date(results, start_date, end_date)
        
        return render_template('results.html', results=results, query=query)
    
    return render_template('search.html')

# 메인 페이지
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # 기본적으로 data 폴더의 분석 결과 로드
    if os.path.exists('data/all_reports_analyzed.csv'):
        search_engine.load_data('data/all_reports_analyzed.csv')
        
    # 또는 인덱스가 있으면 로드
    elif os.path.exists('index/search_index.pkl'):
        search_engine.load_data('index/search_index.pkl')
    
    app.run(debug=True)