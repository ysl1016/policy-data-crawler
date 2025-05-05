from src.crawler.research_institute_crawler import ResearchInstituteCrawler
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

class BOKCrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.bok.or.kr"
    
    def crawl_reports(self, start_page=1, end_page=10, category='research'):
        """한국은행 연구보고서 크롤링"""
        reports = []
        
        try:
            for page in range(start_page, end_page + 1):
                url = f"{self.base_url}/portal/bbs/B0000217/list.do?menuNo=200761&pageIndex={page}"
                
                # 자바스크립트 렌더링이 필요한 경우 Selenium 사용
                self.driver.get(url)
                time.sleep(3)  # 페이지 로딩 대기
                
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                report_items = soup.select('.boardList tbody tr')
                
                for item in report_items:
                    try:
                        cols = item.select('td')
                        if len(cols) >= 4:
                            title_elem = cols[1].select_one('a')
                            title = title_elem.text.strip()
                            link = f"{self.base_url}{title_elem['href']}"
                            date = cols[3].text.strip()
                            
                            # 상세 페이지 접근하여 추가 정보 수집
                            detail = self.get_report_detail(link)
                            
                            report_data = {
                                'title': title,
                                'date': date,
                                'link': link,
                                'abstract': detail.get('abstract', ''),
                                'pdf_link': detail.get('pdf_link', '')
                            }
                            
                            reports.append(report_data)
                            logging.info(f"Crawled BOK: {title}")
                            time.sleep(1)
                    
                    except Exception as e:
                        logging.error(f"Error crawling BOK report: {e}")
                
                logging.info(f"Completed BOK page {page}")
                time.sleep(2)
        
        except Exception as e:
            logging.error(f"Error in BOK crawling: {e}")
        
        return pd.DataFrame(reports)
    
    def get_report_detail(self, url):
        """한국은행 보고서 상세 페이지 크롤링"""
        detail = {}
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 초록 추출
            abstract_section = soup.select_one('.substance')
            if abstract_section:
                detail['abstract'] = abstract_section.text.strip()
            
            # PDF 링크 추출
            pdf_link = soup.select_one('a.fileDown')
            if pdf_link:
                detail['pdf_link'] = f"{self.base_url}{pdf_link['href']}"
        
        except Exception as e:
            logging.error(f"Error getting BOK report detail: {e}")
        
        return detail