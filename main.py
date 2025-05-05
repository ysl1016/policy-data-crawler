import argparse
import os
import pandas as pd
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 커스텀 모듈 임포트
from src.crawler.kdi_crawler import KDICrawler
from src.crawler.bok_crawler import BOKCrawler
from src.processor.pdf_processor import PDFProcessor
from src.analyzer.text_analyzer import TextAnalyzer
from src.search.search_engine import SearchEngine
from src.analyzer.policy_analyzer import PolicyAnalyzer

# 로깅 설정
logging.basicConfig(
    filename=f'policy_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_folders():
    """필요한 폴더 생성"""
    folders = ['data', 'downloads', 'reports', 'index']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logging.info(f"Created folder: {folder}")

def crawl_data(args):
    """데이터 크롤링 처리"""
    logging.info("Starting data crawling")
    
    # KDI 데이터 크롤링
    if args.crawl_kdi or args.crawl_all:
        kdi_crawler = KDICrawler()
        kdi_reports = kdi_crawler.crawl_reports(
            start_page=args.start_page, 
            end_page=args.end_page
        )
        kdi_crawler.save_to_csv(kdi_reports, 'data/kdi_reports.csv')
        kdi_crawler.close()
        logging.info(f"Crawled {len(kdi_reports)} KDI reports")
    
    # BOK 데이터 크롤링
    if args.crawl_bok or args.crawl_all:
        bok_crawler = BOKCrawler()
        bok_reports = bok_crawler.crawl_reports(
            start_page=args.start_page, 
            end_page=args.end_page
        )
        bok_crawler.save_to_csv(bok_reports, 'data/bok_reports.csv')
        bok_crawler.close()
        logging.info(f"Crawled {len(bok_reports)} BOK reports")
    
    logging.info("Finished data crawling")

def process_pdfs(args):
    """PDF 다운로드 및 처리"""
    logging.info("Starting PDF processing")
    processor = PDFProcessor(pdf_dir='downloads')
    
    # KDI PDF 처리
    if args.process_kdi or args.process_all:
        if os.path.exists('data/kdi_reports.csv'):
            kdi_data = pd.read_csv('data/kdi_reports.csv')
            pdf_links = kdi_data['pdf_link'].dropna().tolist()
            filenames = [f"kdi_{i}.pdf" for i in range(len(pdf_links))]
            
            logging.info(f"Processing {len(pdf_links)} KDI PDFs")
            with ThreadPoolExecutor(max_workers=5) as executor:
                kdi_results = list(executor.map(
                    lambda args: processor.extract_best_text(
                        processor.download_pdf(args[0], args[1])
                    ),
                    zip(pdf_links, filenames)
                ))
            
            # 결과 저장
            kdi_data['pdf_text'] = pd.Series(kdi_results)
            kdi_data.to_csv('data/kdi_reports_with_text.csv', index=False)
    
    # BOK PDF 처리
    if args.process_bok or args.process_all:
        if os.path.exists('data/bok_reports.csv'):
            bok_data = pd.read_csv('data/bok_reports.csv')
            pdf_links = bok_data['pdf_link'].dropna().tolist()
            filenames = [f"bok_{i}.pdf" for i in range(len(pdf_links))]
            
            logging.info(f"Processing {len(pdf_links)} BOK PDFs")
            with ThreadPoolExecutor(max_workers=5) as executor:
                bok_results = list(executor.map(
                    lambda args: processor.extract_best_text(
                        processor.download_pdf(args[0], args[1])
                    ),
                    zip(pdf_links, filenames)
                ))
            
            # 결과 저장
            bok_data['pdf_text'] = pd.Series(bok_results)
            bok_data.to_csv('data/bok_reports_with_text.csv', index=False)
    
    logging.info("Finished PDF processing")

def analyze_text(args):
    """텍스트 분석 처리"""
    logging.info("Starting text analysis")
    analyzer = TextAnalyzer()
    
    # 데이터 통합
    all_reports = pd.DataFrame()
    
    if os.path.exists('data/kdi_reports_with_text.csv'):
        kdi_data = pd.read_csv('data/kdi_reports_with_text.csv')
        kdi_data['source'] = 'KDI'
        all_reports = pd.concat([all_reports, kdi_data])
    
    if os.path.exists('data/bok_reports_with_text.csv'):
        bok_data = pd.read_csv('data/bok_reports_with_text.csv')
        bok_data['source'] = 'BOK'
        all_reports = pd.concat([all_reports, bok_data])
    
    if len(all_reports) == 0:
        logging.warning("No data found for analysis")
        return
    
    # 텍스트 칼럼 통합
    all_reports['text'] = all_reports['abstract'].fillna('') + ' ' + all_reports['pdf_text'].fillna('')
    
    # 키워드 추출
    logging.info("Extracting keywords")
    documents = all_reports['text'].fillna('').tolist()
    keywords = analyzer.extract_keywords_tfidf(documents, top_n=args.top_keywords)
    
    # 키워드 저장
    for i, kw_list in enumerate(keywords):
        all_reports.loc[i, 'keywords'] = ', '.join(kw_list)
    
    # 토픽 모델링
    logging.info("Running topic modeling")
    topics, lda_model, corpus, dictionary = analyzer.topic_modeling_lda(
        documents, 
        num_topics=args.num_topics
    )
    
    # 문서 분류
    tokenized_docs = [analyzer.extract_nouns(doc) for doc in documents]
    doc_topics = analyzer.classify_documents(lda_model, corpus, dictionary, tokenized_docs)
    
    # 토픽 정보 저장
    for doc in doc_topics:
        all_reports.loc[doc['doc_index'], 'main_topic'] = doc['main_topic']
        all_reports.loc[doc['doc_index'], 'topic_prob'] = doc['topic_prob']
    
    # 결과 저장
    all_reports.to_csv('data/all_reports_analyzed.csv', index=False)
    logging.info("Saved analysis results")
    
    # 토픽 정보 저장
    topic_info = []
    for i, topic_terms in enumerate(topics):
        topic_info.append({
            'topic_id': i,
            'terms': ', '.join([term for term, prob in topic_terms])
        })
    
    pd.DataFrame(topic_info).to_csv('data/topics.csv', index=False)
    logging.info("Saved topic information")
    
    logging.info("Finished text analysis")

def build_search_index(args):
    """검색 인덱스 구축"""
    logging.info("Building search index")
    
    if not os.path.exists('data/all_reports_analyzed.csv'):
        logging.warning("No analyzed data found for indexing")
        return
    
    all_reports = pd.read_csv('data/all_reports_analyzed.csv')
    
    # 검색 엔진 초기화 및 인덱싱
    search_engine = SearchEngine()
    search_engine.index_documents(all_reports, text_column='text', title_column='title')
    
    # 인덱스 저장
    search_engine.save_index('index/search_index.pkl')
    logging.info("Search index built and saved")

def generate_reports(args):
    """정책 분석 보고서 생성"""
    logging.info("Generating policy reports")
    
    if not os.path.exists('data/all_reports_analyzed.csv'):
        logging.warning("No analyzed data found for report generation")
        return
    
    # 분석기 초기화
    analyzer = PolicyAnalyzer('data/all_reports_analyzed.csv')
    
    # 키워드 요약 생성
    keywords_df = analyzer.generate_keyword_summary('text', top_n=args.top_keywords)
    keywords_df.to_csv('reports/keywords_summary.csv', index=False)
    
    # 워드클라우드 생성
    analyzer.generate_wordcloud('text', output_path='reports/wordcloud.png')
    
    # 키워드 트렌드 분석
    top_keywords = keywords_df['keyword'].head(5).tolist()
    analyzer.compare_keywords_trend('text', top_keywords, date_column='date')
    
    # 최종 보고서 생성
    analyzer.generate_policy_report(output_path='reports/policy_report.html')
    
    logging.info("Policy reports generated")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="정책 자료 크롤링 및 분석 도구")
    
    # 크롤링 관련 인자
    parser.add_argument('--crawl_kdi', action='store_true', help='KDI 자료 크롤링')
    parser.add_argument('--crawl_bok', action='store_true', help='BOK 자료 크롤링')
    parser.add_argument('--crawl_all', action='store_true', help='모든 기관 자료 크롤링')
    parser.add_argument('--start_page', type=int, default=1, help='크롤링 시작 페이지')
    parser.add_argument('--end_page', type=int, default=5, help='크롤링 종료 페이지')
    
    # PDF 처리 관련 인자
    parser.add_argument('--process_kdi', action='store_true', help='KDI PDF 처리')
    parser.add_argument('--process_bok', action='store_true', help='BOK PDF 처리')
    parser.add_argument('--process_all', action='store_true', help='모든 PDF 처리')
    
    # 분석 관련 인자
    parser.add_argument('--analyze', action='store_true', help='텍스트 분석 수행')
    parser.add_argument('--top_keywords', type=int, default=20, help='추출할 상위 키워드 수')
    parser.add_argument('--num_topics', type=int, default=5, help='토픽 모델링에서 추출할 토픽 수')
    
    # 검색 인덱스 관련 인자
    parser.add_argument('--build_index', action='store_true', help='검색 인덱스 구축')
    
    # 보고서 생성 관련 인자
    parser.add_argument('--generate_reports', action='store_true', help='정책 분석 보고서 생성')
    
    # 전체 파이프라인 실행 관련 인자
    parser.add_argument('--run_all', action='store_true', help='전체 파이프라인 실행')
    
    args = parser.parse_args()
    
    # 필요한 폴더 생성
    setup_folders()
    
    # 전체 파이프라인 실행 플래그 설정
    if args.run_all:
        args.crawl_all = True
        args.process_all = True
        args.analyze = True
        args.build_index = True
        args.generate_reports = True
    
    # 단계별 실행
    if args.crawl_kdi or args.crawl_bok or args.crawl_all:
        crawl_data(args)
    
    if args.process_kdi or args.process_bok or args.process_all:
        process_pdfs(args)
    
    if args.analyze:
        analyze_text(args)
    
    if args.build_index:
        build_search_index(args)
    
    if args.generate_reports:
        generate_reports(args)
    
    logging.info("All tasks completed")

if __name__ == "__main__":
    main()