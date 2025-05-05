from src.crawler.research_institute_crawler import ResearchInstituteCrawler
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BOKCrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.bok.or.kr"
        
        # 디버깅을 위한 디렉토리 생성
        self.debug_dir = "debug/bok"
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def crawl_reports(self, start_page=1, end_page=10, category='research'):
        """한국은행 연구보고서 크롤링"""
        reports = []
        
        try:
            for page in range(start_page, end_page + 1):
                # 연구보고서 페이지 URL (필요시 URL 업데이트)
                url = f"{self.base_url}/portal/bbs/B0000217/list.do?menuNo=200761&pageIndex={page}"
                
                logging.info(f"BOK 페이지 접근 중: {url}")
                
                try:
                    # Selenium을 사용하여 페이지 로드
                    if not self.driver:
                        logging.error("Selenium 웹드라이버가 초기화되지 않았습니다")
                        break
                    
                    self.driver.get(url)
                    
                    # 페이지 로딩 대기 시간 증가
                    try:
                        # 테이블 요소가 로드될 때까지 대기
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
                        )
                    except Exception as e:
                        logging.warning(f"페이지 로딩 대기 중 시간 초과: {e}")
                    
                    # 자바스크립트 실행 대기
                    time.sleep(5)
                    
                    # 페이지 소스 가져오기
                    html = self.driver.page_source
                    
                    # 디버깅용 페이지 저장
                    with open(f"{self.debug_dir}/page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 여러 가능한 보고서 목록 선택자 시도
                    selectors = [
                        '.boardList tbody tr',
                        '.board_list tbody tr',
                        '.board-list tbody tr',
                        'table tbody tr'
                    ]
                    
                    report_items = []
                    for selector in selectors:
                        report_items = soup.select(selector)
                        if report_items:
                            logging.info(f"선택자 '{selector}'로 {len(report_items)}개 항목 발견")
                            break
                    
                    if not report_items:
                        logging.warning(f"페이지 {page}에서 보고서 항목을 찾을 수 없습니다")
                        # 페이지 구조 분석을 위한 디버깅 정보
                        tables = soup.find_all('table')
                        logging.info(f"페이지 내 테이블 수: {len(tables)}")
                        if tables:
                            for i, table in enumerate(tables):
                                rows = table.find_all('tr')
                                logging.info(f"테이블 {i+1}: {len(rows)}개 행")
                        continue
                    
                    for item in report_items:
                        try:
                            # 모든 열 가져오기
                            cols = item.select('td')
                            if len(cols) < 2:
                                continue
                            
                            # 제목 추출
                            title_elem = None
                            for col in cols:
                                a_tag = col.select_one('a')
                                if a_tag:
                                    title_elem = a_tag
                                    break
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.text.strip()
                            
                            # 링크 추출
                            link = f"{self.base_url}{title_elem['href']}" if title_elem.has_attr('href') else ""
                            if not link:
                                continue
                            
                            # 날짜 추출 - 일반적으로 마지막 열이나 날짜 클래스가 있는 열
                            date = ""
                            for col in reversed(cols):  # 마지막 열부터 검색
                                date_text = col.text.strip()
                                # 날짜 형식 검사 (YYYY.MM.DD, YYYY-MM-DD 등)
                                if len(date_text) >= 8 and (date_text.count('.') == 2 or date_text.count('-') == 2):
                                    date = date_text
                                    break
                            
                            # 상세 페이지 접근하여 추가 정보 수집
                            logging.info(f"상세 페이지 접근 중: {link}")
                            detail = self.get_report_detail(link)
                            
                            report_data = {
                                'title': title,
                                'date': date,
                                'link': link,
                                'abstract': detail.get('abstract', ''),
                                'pdf_link': detail.get('pdf_link', ''),
                                'author': detail.get('author', '')
                            }
                            
                            reports.append(report_data)
                            logging.info(f"보고서 크롤링 성공: {title}")
                            
                            # 서버 부담 방지를 위한 지연
                            time.sleep(2)
                            
                        except Exception as e:
                            logging.error(f"보고서 항목 처리 중 오류: {e}")
                    
                    logging.info(f"BOK 페이지 {page} 완료")
                    time.sleep(3)  # 페이지 간 지연
                    
                except Exception as e:
                    logging.error(f"BOK 페이지 {page} 처리 중 오류: {e}")
                    import traceback
                    logging.error(traceback.format_exc())
                
        except Exception as e:
            logging.error(f"BOK 크롤링 중 오류: {e}")
            
        logging.info(f"BOK 크롤링 완료: {len(reports)}개 보고서")
        return pd.DataFrame(reports) if reports else pd.DataFrame()
    
    def get_report_detail(self, url):
        """한국은행 보고서 상세 페이지 크롤링"""
        detail = {}
        
        try:
            if not self.driver:
                logging.error("Selenium 웹드라이버가 초기화되지 않았습니다")
                return detail
            
            logging.info(f"상세 정보 요청 중: {url}")
            self.driver.get(url)
            
            # 페이지 로딩 대기
            time.sleep(5)
            
            # 페이지 소스 가져오기
            html = self.driver.page_source
            
            # 디버깅용 상세 페이지 저장
            detail_filename = f"{self.debug_dir}/detail_{url.split('/')[-1].split('?')[0]}.html"
            with open(detail_filename, "w", encoding="utf-8") as f:
                f.write(html)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 초록/내용 추출 - 여러 가능한 선택자 시도
            abstract_selectors = [
                '.substance',
                '.content',
                '.board-content',
                '.board-view-content',
                '.contentArea',
                'div.content'
            ]
            
            for selector in abstract_selectors:
                abstract_section = soup.select_one(selector)
                if abstract_section:
                    detail['abstract'] = abstract_section.text.strip()
                    logging.info(f"초록 추출 성공: {selector}")
                    break
            
            # 저자 정보 추출 시도
            author_selectors = [
                '.author',
                '.writer',
                '.board-view-writer',
                'span.name'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    detail['author'] = author_elem.text.strip()
                    logging.info(f"저자 추출 성공: {selector}")
                    break
            
            # PDF 링크 추출
            pdf_selectors = [
                'a.fileDown',
                'a[href*=".pdf"]',
                '.fileDown a',
                '.download a',
                '.file-list a'
            ]
            
            for selector in pdf_selectors:
                pdf_links = soup.select(selector)
                for pdf_link in pdf_links:
                    if pdf_link and pdf_link.has_attr('href'):
                        href = pdf_link['href']
                        if href and ('.pdf' in href.lower() or 'download' in href.lower()):
                            detail['pdf_link'] = f"{self.base_url}{href}" if not href.startswith('http') else href
                            logging.info(f"PDF 링크 추출 성공: {selector}")
                            break
                
                if 'pdf_link' in detail:
                    break
            
        except Exception as e:
            logging.error(f"상세 정보 조회 중 오류: {e}")
            
        return detail