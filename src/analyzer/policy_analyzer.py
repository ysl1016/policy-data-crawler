import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
from konlpy.tag import Okt
from collections import Counter
import os

class PolicyAnalyzer:
    def __init__(self, data_path=None):
        self.data = None
        self.okt = Okt()
        
        if data_path:
            self.load_data(data_path)
    
    def load_data(self, data_path):
        """데이터 로드"""
        if data_path.endswith('.csv'):
            self.data = pd.read_csv(data_path)
        elif data_path.endswith('.xlsx'):
            self.data = pd.read_excel(data_path)
        else:
            raise ValueError("Unsupported file format")
    
    def generate_keyword_summary(self, text_column, top_n=50):
        """키워드 빈도 요약"""
        all_nouns = []
        
        for text in self.data[text_column].fillna(''):
            nouns = self.okt.nouns(str(text))
            all_nouns.extend([noun for noun in nouns if len(noun) > 1])
        
        # 키워드 빈도 계산
        keyword_freq = Counter(all_nouns).most_common(top_n)
        
        # 데이터프레임으로 변환
        keywords_df = pd.DataFrame(keyword_freq, columns=['keyword', 'frequency'])
        
        return keywords_df
    
    def generate_wordcloud(self, text_column, output_path='wordcloud.png'):
        """워드클라우드 생성"""
        combined_text = ' '.join(self.data[text_column].fillna('').astype(str))
        
        # 명사 추출
        nouns = self.okt.nouns(combined_text)
        noun_text = ' '.join([noun for noun in nouns if len(noun) > 1])
        
        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path='NanumGothic.ttf',  # 한글 폰트 경로
            width=800,
            height=600,
            background_color='white'
        ).generate(noun_text)
        
        # 저장
        plt.figure(figsize=(10, 8))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def analyze_trend_by_year(self, text_column, keyword, date_column='date'):
        """연도별 키워드 트렌드 분석"""
        # 날짜 형식 변환
        self.data['year'] = pd.to_datetime(self.data[date_column]).dt.year
        
        # 키워드 포함 여부 확인
        self.data['contains_keyword'] = self.data[text_column].fillna('').astype(str).str.contains(keyword)
        
        # 연도별 그룹화 및 비율 계산
        yearly_counts = self.data.groupby('year')['contains_keyword'].agg(['count', 'sum'])
        yearly_counts['ratio'] = yearly_counts['sum'] / yearly_counts['count'] * 100
        
        # 시각화
        plt.figure(figsize=(12, 6))
        sns.lineplot(x=yearly_counts.index, y=yearly_counts['ratio'])
        plt.title(f'Yearly Trend for Keyword: {keyword}')
        plt.xlabel('Year')
        plt.ylabel('Occurrence Ratio (%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(f'{keyword}_trend.png')
        plt.close()
        
        return yearly_counts
    
    def compare_keywords_trend(self, text_column, keywords, date_column='date'):
        """여러 키워드 트렌드 비교 분석"""
        # 날짜 형식 변환
        self.data['year'] = pd.to_datetime(self.data[date_column]).dt.year
        
        results = {}
        plt.figure(figsize=(14, 8))
        
        for keyword in keywords:
            # 키워드 포함 여부 확인
            self.data[f'contains_{keyword}'] = self.data[text_column].fillna('').astype(str).str.contains(keyword)
            
            # 연도별 그룹화 및 비율 계산
            yearly_counts = self.data.groupby('year')[f'contains_{keyword}'].agg(['count', 'sum'])
            yearly_counts['ratio'] = yearly_counts['sum'] / yearly_counts['count'] * 100
            
            # 결과 저장
            results[keyword] = yearly_counts
            
            # 시각화에 추가
            sns.lineplot(x=yearly_counts.index, y=yearly_counts['ratio'], label=keyword)
        
        plt.title('Yearly Trend Comparison for Keywords')
        plt.xlabel('Year')
        plt.ylabel('Occurrence Ratio (%)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig('keywords_comparison.png')
        plt.close()
        
        return results
    
    def generate_policy_report(self, output_path='policy_report.html'):
        """정책 분석 보고서 생성"""
        if self.data is None:
            raise ValueError("No data loaded")
        
        # 기본 통계 수집
        total_documents = len(self.data)
        year_range = (self.data['year'].min(), self.data['year'].max()) if 'year' in self.data.columns else ('Unknown', 'Unknown')
        
        # HTML 보고서 생성
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>정책 데이터 분석 보고서</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .stats {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .chart {{ margin: 20px 0; }}
                .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>정책 데이터 분석 보고서</h1>
                <div class="stats">
                    <h2>기본 통계</h2>
                    <p>총 문서 수: {total_documents}</p>
                    <p>수집 연도 범위: {year_range[0]} - {year_range[1]}</p>
                </div>
                
                <h2>주요 키워드 분석</h2>
                <div id="keyword-table">
                    <!-- 키워드 빈도 테이블 추가 -->
                </div>
                
                <h2>시각화</h2>
                <div class="chart">
                    <h3>워드클라우드</h3>
                    <img src="wordcloud.png" alt="Word Cloud" style="max-width: 100%;">
                </div>
                
                <div class="chart">
                    <h3>주요 키워드 트렌드</h3>
                    <img src="keywords_comparison.png" alt="Keyword Trends" style="max-width: 100%;">
                </div>
                
                <div class="footer">
                    <p>생성일: {pd.Timestamp.now().strftime('%Y-%m-%d')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path