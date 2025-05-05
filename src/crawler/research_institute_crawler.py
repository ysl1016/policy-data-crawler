import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class ResearchInstituteCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        self.session = requests.Session()
        
        # SSL 인증서 검증 비활성화 (주의: 보안상 위험할 수 있음)
        self.session.verify = False
        
        # 경고 메시지 무시
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Selenium 설정 (자바스크립트 렌더링 필요 시)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # SSL 인증서 검증 비활성화 (Selenium)
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        
        # 브라우저 창 확인을 위해 필요시 헤드리스 모드 비활성화 (디버깅 시)
        # chrome_options.headless = False
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logging.info("Selenium 웹드라이버 초기화 성공")
        except Exception as e:
            logging.error(f"Selenium 웹드라이버 초기화 실패: {e}")
            self.driver = None
    
    def save_to_csv(self, dataframe, filename):
        """수집 데이터 CSV 저장"""
        try:
            # 빈 데이터프레임 체크
            if dataframe is None or len(dataframe) == 0:
                logging.warning(f"저장할 데이터가 없습니다: {filename}")
                # 최소한의 헤더만 있는 파일 생성
                if dataframe is not None:
                    dataframe.to_csv(filename, index=False, encoding='utf-8-sig')
                else:
                    pd.DataFrame(columns=['title', 'author', 'date', 'link', 'abstract', 'pdf_link']).to_csv(
                        filename, index=False, encoding='utf-8-sig')
                return
            
            dataframe.to_csv(filename, index=False, encoding='utf-8-sig')
            logging.info(f"{len(dataframe)}개 항목이 {filename}에 저장되었습니다")
        except Exception as e:
            logging.error(f"CSV 저장 오류: {e}")
    
    def save_to_database(self, dataframe, table_name):
        """데이터베이스에 저장"""
        from sqlalchemy import create_engine
        
        try:
            engine = create_engine('sqlite:///research_data.db')
            dataframe.to_sql(table_name, engine, if_exists='append', index=False)
            logging.info(f"데이터가 {table_name} 테이블에 저장되었습니다")
        
        except Exception as e:
            logging.error(f"데이터베이스 오류: {e}")
    
    def close(self):
        """리소스 정리"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("Selenium 웹드라이버 종료 성공")
            except Exception as e:
                logging.error(f"Selenium 웹드라이버 종료 실패: {e}")
        
        self.session.close()
        logging.info("요청 세션 종료 성공")