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
                print(f"CSV 파일 로드 시도: {data_path}")
                self.documents = pd.read_csv(data_path)
                print(f"로드된 문서 수: {len(self.documents)}")
            elif data_path.endswith('.pkl'):
                print(f"PKL 파일 로드 시도: {data_path}")
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents')
                    self.tfidf_matrix = data.get('tfidf_matrix')
                    self.vectorizer = data.get('vectorizer', self.vectorizer)
                print(f"PKL에서 로드된 문서 수: {len(self.documents) if self.documents is not None else 0}")
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def index_documents(self, documents, text_column='text', title_column='title'):
        """문서 인덱싱"""
        self.documents = documents
        
        # 텍스트 전처리 - 빈 값은 빈 문자열로 변환
        processed_texts = documents[text_column].fillna('').astype(str).tolist()
        
        # 디버깅 정보
        print(f"인덱싱할 문서 수: {len(documents)}")
        print(f"첫 번째 문서 텍스트 샘플: {processed_texts[0][:100]}...")
        
        # TF-IDF 행렬 생성
        self.tfidf_matrix = self.vectorizer.fit_transform(processed_texts)
        
        print(f"TF-IDF 행렬 크기: {self.tfidf_matrix.shape}")
        print(f"추출된 특성 수: {len(self.vectorizer.get_feature_names_out())}")
        print(f"인덱싱된 문서 수: {len(documents)}")
    
    def save_index(self, filepath):
        """인덱스 저장"""
        if self.tfidf_matrix is None:
            print("저장할 인덱스가 없습니다. 먼저 문서를 인덱싱하세요.")
            return
            
        data = {
            'documents': self.documents,
            'tfidf_matrix': self.tfidf_matrix,
            'vectorizer': self.vectorizer
        }
        
        try:
            # 디렉토리 확인 및 생성
            dir_path = os.path.dirname(filepath)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"인덱스가 {filepath}에 저장되었습니다.")
        except Exception as e:
            print(f"인덱스 저장 오류: {e}")
    
    def search(self, query, top_n=10):
        """쿼리 검색"""
        if self.tfidf_matrix is None:
            print("인덱싱된 문서가 없습니다. 먼저 문서를 인덱싱하세요.")
            return []
        
        # 쿼리 디버깅 출력
        print(f"검색 쿼리: '{query}'")
        print(f"검색할 문서 수: {self.tfidf_matrix.shape[0]}")
        
        try:
            # 쿼리 벡터화
            query_vector = self.vectorizer.transform([query])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # 디버깅: 유사도 값 분포
            print(f"유사도 값 범위: {similarities.min():.4f} ~ {similarities.max():.4f}")
            print(f"평균 유사도: {similarities.mean():.4f}")
            
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
            
            print(f"검색 결과 수: {len(results)}")
            return results
            
        except Exception as e:
            print(f"검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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