import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class SearchEngine:
    def __init__(self, data_path=None):
        self.vectorizer = TfidfVectorizer(max_features=10000)
        self.tfidf_matrix = None
        self.documents = None
        
        if data_path and os.path.exists(data_path):
            self.load_data(data_path)
    
    def load_data(self, data_path):
        """데이터 로드"""
        try:
            if data_path.endswith('.csv'):
                self.documents = pd.read_csv(data_path)
            elif data_path.endswith('.pkl'):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents')
                    self.tfidf_matrix = data.get('tfidf_matrix')
                    self.vectorizer = data.get('vectorizer', self.vectorizer)
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def index_documents(self, documents, text_column='text', title_column='title'):
        """문서 인덱싱"""
        self.documents = documents
        
        # 텍스트 전처리
        processed_texts = documents[text_column].fillna('').astype(str).tolist()
        
        # TF-IDF 행렬 생성
        self.tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
        
        print(f"Indexed {len(documents)} documents")
    
    def save_index(self, filepath):
        """인덱스 저장"""
        data = {
            'documents': self.documents,
            'tfidf_matrix': self.tfidf_matrix,
            'vectorizer': self.vectorizer
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Index saved to {filepath}")
    
    def search(self, query, top_n=10):
        """쿼리 검색"""
        if self.tfidf_matrix is None:
            print("No indexed documents. Please index documents first.")
            return []
        
        # 쿼리 벡터화
        query_vector = self.vectorizer.transform([query])
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # 유사도 기준 정렬
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        # 결과 반환
        results = []
        for idx in top_indices:
            result = {
                'index': idx,
                'score': similarities[idx]
            }
            
            # 문서 메타데이터 추가
            for col in self.documents.columns:
                result[col] = self.documents.iloc[idx][col]
            
            results.append(result)
        
        return results
    
    def keyword_search(self, keywords, top_n=10):
        """키워드 기반 검색"""
        if isinstance(keywords, str):
            keywords = [keywords]
        
        # 키워드를 공백으로 구분된 하나의 쿼리로 변환
        query = ' '.join(keywords)
        
        return self.search(query, top_n)
    
    def filter_by_date(self, results, start_date=None, end_date=None, date_column='date'):
        """날짜 기준 필터링"""
        if start_date is None and end_date is None:
            return results
        
        filtered = []
        for result in results:
            date_str = result.get(date_column, '')
            
            try:
                # 날짜 형식 변환
                date = pd.to_datetime(date_str)
                
                # 날짜 범위 검사
                if start_date and date < pd.to_datetime(start_date):
                    continue
                if end_date and date > pd.to_datetime(end_date):
                    continue
                
                filtered.append(result)
            
            except:
                # 날짜 변환 실패 시 무시
                continue
        
        return filtered