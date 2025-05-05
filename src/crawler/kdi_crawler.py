from src.crawler.research_institute_crawler import ResearchInstituteCrawler
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import os

class KDICrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.kdi.re.kr"
        
        # 디버깅을 위한 디렉토리 생성
        self.debug_dir = "debug/kdi"
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def crawl_reports(self, start_page=1, end_page=10, category='정책연구'):
        """KDI 연구보고서 크롤링"""
        reports = []
        
        try:
            for page in range(start_page, end_page + 1):
                url = f"{self.base_url}/research/reportList?page={page}&category={category}"
                logging.info(f"KDI 페이지 접근 중: {url}")
                
                try:
                    # 웹 페이지 요청
                    response = self.session.get(url, headers=self.headers, timeout=30)
                    
                    # 응답 상태 확인
                    if response.status_code != 200:
                        logging.error(f"HTTP 오류: {response.status_code}")
                        continue
                    
                    # 디버깅용 페이지 저장
                    with open(f"{self.debug_dir}/page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 보고서 목록 선택자 - 여러 가능한 선택자 시도
                    report_items = soup.select('.board-list-box .item')
                    
                    # 선택자가 변경되었을 경우를 대비한 대체 선택자 시도
                    if not report_items:
                        logging.warning(f"기본 선택자로 항목을 찾지 못함, 대체 선택자 시도 중")
                        
                        # 다른 가능한 선택자들 시도
                        selectors = [
                            '.board-list .item', 
                            '.board-list tr', 
                            '.news-list .item',
                            '.report-list .item'
                        ]
                        
                        for selector in selectors:
                            report_items = soup.select(selector)
                            if report_items:
                                logging.info(f"대체 선택자 성공: {selector}, 항목 수: {len(report_items)}")
                                break
                    
                    logging.info(f"페이지 {page}에서 {len(report_items)}개 항목 발견")
                    
                    for item in report_items:
                        try:
                            # 제목 추출 시도
                            title_elem = item.select_one('.tit') or item.select_one('a') or item.select_one('h3')
                            if not title_elem:
                                logging.warning("제목 요소를 찾을 수 없음, 다음 항목으로 건너뜀")
                                continue
                                
                            title = title_elem.text.strip()
                            
                            # 링크 추출
                            link_elem = item.select_one('a')
                            if not link_elem or not link_elem.has_attr('href'):
                                logging.warning(f"링크를 찾을 수 없음: {title}")
                                continue
                                
                            link = f"{self.base_url}{link_elem['href']}"
                            
                            # 날짜 추출
                            date_elem = item.select_one('.date') or item.select_one('.board-date')
                            date = date_elem.text.strip() if date_elem else ""
                            
                            # 저자 추출
                            author_elem = item.select_one('.name') or item.select_one('.author')
                            author = author_elem.text.strip() if author_elem else "저자 미상"
                            
                            # 상세 페이지 접근하여 초록 및 키워드 추출
                            logging.info(f"상세 페이지 접근 중: {link}")
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
                            logging.info(f"보고서 크롤링 성공: {title}")
                            
                            # 서버 부담 방지를 위한 지연
                            time.sleep(2)
                            
                        except Exception as e:
                            logging.error(f"보고서 항목 처리 중 오류: {e}")
                    
                    logging.info(f"페이지 {page} 완료")
                    time.sleep(3)  # 페이지 간 지연
                    
                except Exception as e:
                    logging.error(f"페이지 {page} 처리 중 오류: {e}")
                
        except Exception as e:
            logging.error(f"KDI 크롤링 중 오류: {e}")
            
        logging.info(f"KDI 크롤링 완료: {len(reports)}개 보고서")
        return pd.DataFrame(reports) if reports else pd.DataFrame()
    
    def get_report_detail(self, url):
        """KDI 보고서 상세 페이지 크롤링"""
        detail = {}
        
        try:
            logging.info(f"상세 정보 요청 중: {url}")
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                logging.error(f"상세 페이지 HTTP 오류: {response.status_code}")
                return detail
            
            # 디버깅용 상세 페이지 저장
            detail_filename = f"{self.debug_dir}/detail_{url.split('/')[-1]}.html"
            with open(detail_filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 초록 추출 - 여러 가능한 선택자 시도
            abstract_selectors = [
                '.report-view-contents', 
                '.view-contents', 
                '.article-content',
                '.content-area'
            ]
            
            for selector in abstract_selectors:
                abstract_section = soup.select_one(selector)
                if abstract_section:
                    detail['abstract'] = abstract_section.text.strip()
                    logging.info(f"초록 추출 성공: {selector}")
                    break
            
            # 키워드 추출
            keyword_selectors = [
                '.keyword-item',
                '.tag-item',
                '.keywords span'
            ]
            
            for selector in keyword_selectors:
                keyword_section = soup.select(selector)
                if keyword_section:
                    detail['keywords'] = [keyword.text.strip() for keyword in keyword_section]
                    logging.info(f"키워드 추출 성공: {selector}, {len(detail['keywords'])}개")
                    break
            
            # PDF 링크 추출
            pdf_selectors = [
                'a.report-pdf-download',
                'a[href*=".pdf"]',
                '.file-download a'
            ]
            
            for selector in pdf_selectors:
                pdf_link = soup.select_one(selector)
                if pdf_link and pdf_link.has_attr('href'):
                    href = pdf_link['href']
                    detail['pdf_link'] = f"{self.base_url}{href}" if not href.startswith('http') else href
                    logging.info(f"PDF 링크 추출 성공: {selector}")
                    break
            
        except Exception as e:
            logging.error(f"상세 정보 조회 중 오류: {e}")
            
        return detail