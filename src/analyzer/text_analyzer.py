import pandas as pd
import numpy as np
import re
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import nltk
from gensim import corpora, models

class TextAnalyzer:
    def __init__(self):
        self.okt = Okt()  # 한국어 형태소 분석기
        nltk.download('punkt')
        nltk.download('stopwords')
    
    def preprocess_text(self, text):
        """텍스트 전처리"""
        # 특수문자 제거
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 숫자 제거
        text = re.sub(r'\d+', ' ', text)
        
        # 여러 공백을 하나로 변경
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_nouns(self, text):
        """한국어 명사 추출"""
        return self.okt.nouns(text)
    
    def extract_keywords_tfidf(self, documents, top_n=20):
        """TF-IDF 기반 키워드 추출"""
        # 텍스트 전처리
        processed_docs = [self.preprocess_text(doc) for doc in documents]
        
        # 명사 추출
        tokenized_docs = [' '.join(self.extract_nouns(doc)) for doc in processed_docs]
        
        # TF-IDF 계산
        vectorizer = TfidfVectorizer(max_features=1000, min_df=2)
        tfidf_matrix = vectorizer.fit_transform(tokenized_docs)
        
        # 주요 키워드 추출
        feature_names = vectorizer.get_feature_names_out()
        keywords = []
        
        for i in range(len(tokenized_docs)):
            # 문서별 TF-IDF 점수
            tfidf_scores = tfidf_matrix[i].toarray()[0]
            
            # 점수와 단어 쌍으로 만들어 정렬
            word_scores = [(feature_names[j], tfidf_scores[j]) for j in range(len(feature_names))]
            word_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 키워드 추출
            doc_keywords = [word for word, score in word_scores[:top_n]]
            keywords.append(doc_keywords)
        
        return keywords
    
    def topic_modeling_lda(self, documents, num_topics=5):
        """LDA 토픽 모델링"""
        # 텍스트 전처리 및 토큰화
        processed_docs = [self.preprocess_text(doc) for doc in documents]
        tokenized_docs = [self.extract_nouns(doc) for doc in processed_docs]
        
        # 사전 및 코퍼스 생성
        dictionary = corpora.Dictionary(tokenized_docs)
        corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]
        
        # LDA 모델 훈련
        lda_model = models.LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            passes=10,
            alpha='auto',
            per_word_topics=True
        )
        
        # 토픽 추출
        topics = []
        for i in range(num_topics):
            # 각 토픽의 상위 10개 단어 추출
            terms = lda_model.get_topic_terms(i, 10)
            topic_terms = [(dictionary[term_id], prob) for term_id, prob in terms]
            topics.append(topic_terms)
        
        return topics, lda_model, corpus, dictionary
    
    def classify_documents(self, lda_model, corpus, dictionary, tokenized_docs):
        """문서 분류"""
        document_topics = []
        
        for i, doc_bow in enumerate(corpus):
            # 문서의 토픽 분포 계산
            topic_dist = lda_model.get_document_topics(doc_bow)
            # 주요 토픽 선택
            main_topic = max(topic_dist, key=lambda x: x[1])
            
            document_topics.append({
                'doc_index': i,
                'tokens': tokenized_docs[i],
                'main_topic': main_topic[0],
                'topic_prob': main_topic[1],
                'topic_dist': topic_dist
            })
        
        return document_topics