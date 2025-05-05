from src.crawler.research_institute_crawler import ResearchInstituteCrawler
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

class KDICrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.kdi.re.kr"
    
    def crawl_reports(self, start_page=1, end_page=10, category='정책연구'):
        """KDI 연구보고서 크롤링"""
        reports = []
        
        try:
            for page in range(start_page, end_page + 1):
                url = f"{self.base_url}/research/reportList?page={page}&category={category}"
                response = self.session.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    report_items = soup.select('.board-list-box .item')
                    
                    for item in report_items:
                        try:
                            title = item.select_one('.tit').text.strip()
                            link = f"{self.base_url}{item.select_one('a')['href']}"
                            date = item.select_one('.date').text.strip()
                            author = item.select_one('.name').text.strip() if item.select_one('.name') else "저자 미상"
                            
                            # 상세 페이지 접근하여 초록 및 키워드 추출
                            detail = self.get_report_detail(link)
                            
                            report_data = {
                                'title': title,
                                'author': author,
                                'date': date,
                                'link': link,
                                'abstract': detail.get('abstract', ''),
                                'keywords': detail.get('keywords', []),
                                'pdf_link': detail.get('pdf_link', '')
                            }
                            
                            reports.append(report_data)
                            logging.info(f"Crawled: {title}")
                            time.sleep(1)  # 서버 부하 방지
                            
                        except Exception as e:
                            logging.error(f"Error crawling report: {e}")
                
                logging.info(f"Completed page {page}")
                time.sleep(2)  # 페이지 간 대기
                
        except Exception as e:
            logging.error(f"Error in KDI crawling: {e}")
            
        return pd.DataFrame(reports)
    
    def get_report_detail(self, url):
        """KDI 보고서 상세 페이지 크롤링"""
        detail = {}
        
        try:
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 초록 추출
                abstract_section = soup.select_one('.report-view-contents')
                if abstract_section:
                    detail['abstract'] = abstract_section.text.strip()
                
                # 키워드 추출
                keyword_section = soup.select('.keyword-item')
                if keyword_section:
                    detail['keywords'] = [keyword.text.strip() for keyword in keyword_section]
                
                # PDF 링크 추출
                pdf_link = soup.select_one('a.report-pdf-download')
                if pdf_link:
                    detail['pdf_link'] = f"{self.base_url}{pdf_link['href']}"
        
        except Exception as e:
            logging.error(f"Error getting report detail: {e}")
            
        return detail