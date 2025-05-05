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
        
        # Selenium 설정 (자바스크립트 렌더링 필요 시)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def save_to_csv(self, dataframe, filename):
        """수집 데이터 CSV 저장"""
        dataframe.to_csv(filename, index=False, encoding='utf-8-sig')
        logging.info(f"Saved data to {filename}")
    
    def save_to_database(self, dataframe, table_name):
        """데이터베이스에 저장"""
        from sqlalchemy import create_engine
        
        try:
            engine = create_engine('sqlite:///research_data.db')
            dataframe.to_sql(table_name, engine, if_exists='append', index=False)
            logging.info(f"Saved data to database table: {table_name}")
        
        except Exception as e:
            logging.error(f"Database error: {e}")
    
    def close(self):
        """리소스 정리"""
        self.driver.quit()
        self.session.close()