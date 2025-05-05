import time
import logging
import pandas as pd
from bs4 import BeautifulSoup

class KDICrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        self.selectors = self.config.get('kdi_selectors', [
            '.board-list .item',
            '.board-list-box .item',
            'tr',
            '.news-list .item',
            '.report-list .item'
        ])
        self.abstract_selectors = self.config.get('kdi_abstract_selectors', [
            '.report-view-contents',
            '.view-contents',
            '.article-content',
            '.content-area',
            '.summary',
            '.abstract',
        ])
        self.keyword_selectors = self.config.get('kdi_keyword_selectors', [
            '.keyword-item',
            '.tag-item',
            '.keywords span',
            '.keyword',
        ])
        self.pdf_selectors = self.config.get('kdi_pdf_selectors', [
            'a.report-pdf-download',
            'a[href*=".pdf"]',
            '.file-download a',
            'a[href$=".pdf"]',
        ])
        self.max_retries = 3
        self.delay = 2

    def crawl_reports(self, start_page=1, end_page=10, category='정책연구'):
        """KDI 연구보고서 크롤링 (실시간성 및 신뢰성 강화)"""
        reports = []
        for page in range(start_page, end_page + 1):
            url = f"{self.base_url}/research/reportList?page={page}&category={category}"
            logging.info(f"KDI 페이지 접근 중: {url}")
            response = self._request_with_retry(url)
            if not response:
                logging.error(f"페이지 요청 실패: {url}")
                continue
            with open(f"{self.debug_dir}/page_{page}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            report_items = self._select_with_fallback(soup, self.selectors, url)
            if not report_items:
                logging.warning(f"항목 selector 실패: {url}")
                continue
            for item in report_items:
                try:
                    title_elem = item.select_one('.tit') or item.select_one('a') or item.select_one('h3')
                    if not title_elem:
                        logging.warning("제목 요소를 찾을 수 없음, 다음 항목으로 건너뜀")
                        continue
                    title = title_elem.text.strip()
                    link_elem = item.select_one('a')
                    if not link_elem or not link_elem.has_attr('href'):
                        logging.warning(f"링크를 찾을 수 없음: {title}")
                        continue
                    link = f"{self.base_url}{link_elem['href']}"
                    date_elem = item.select_one('.date') or item.select_one('.board-date')
                    date = date_elem.text.strip() if date_elem else ""
                    author_elem = item.select_one('.name') or item.select_one('.author')
                    author = author_elem.text.strip() if author_elem else "저자 미상"
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
                    time.sleep(self.delay)
                except Exception as e:
                    logging.error(f"보고서 항목 처리 중 오류: {e}")
            logging.info(f"페이지 {page} 완료")
            time.sleep(self.delay)
        logging.info(f"KDI 크롤링 완료: {len(reports)}개 보고서")
        return pd.DataFrame(reports) if reports else pd.DataFrame()

    def get_report_detail(self, url):
        """KDI 보고서 상세 페이지 크롤링 (신뢰성 강화)"""
        detail = {}
        response = self._request_with_retry(url)
        if not response:
            logging.error(f"상세 페이지 요청 실패: {url}")
            return detail
        detail_filename = f"{self.debug_dir}/detail_{url.split('/')[-1]}.html"
        with open(detail_filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 초록 추출
        for selector in self.abstract_selectors:
            abstract_section = soup.select_one(selector)
            if abstract_section:
                detail['abstract'] = abstract_section.text.strip()
                logging.info(f"초록 추출 성공: {selector}")
                break
        # 키워드 추출
        for selector in self.keyword_selectors:
            keyword_section = soup.select(selector)
            if keyword_section:
                detail['keywords'] = [keyword.text.strip() for keyword in keyword_section]
                logging.info(f"키워드 추출 성공: {selector}, {len(detail['keywords'])}개")
                break
        # PDF 링크 추출
        for selector in self.pdf_selectors:
            pdf_link = soup.select_one(selector)
            if pdf_link and pdf_link.has_attr('href'):
                href = pdf_link['href']
                detail['pdf_link'] = f"{self.base_url}{href}" if not href.startswith('http') else href
                logging.info(f"PDF 링크 추출 성공: {selector}")
                break
        return detail

    def crawl_reports_by_keyword(self, keyword, start_page=1, end_page=3, category='정책연구'):
        """키워드 기반 KDI 연구보고서 실시간 크롤링 (신뢰성 강화)"""
        reports = []
        for page in range(start_page, end_page + 1):
            url = f"https://www.kdi.re.kr/research/reportList?page={page}&category={category}"
            response = self._request_with_retry(url)
            if not response:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            report_items = self._select_with_fallback(soup, self.selectors, url)
            for item in report_items:
                try:
                    title_elem = item.select_one('.tit') or item.select_one('a') or item.select_one('h3')
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    if keyword not in title:
                        continue
                    link_elem = item.select_one('a')
                    if not link_elem or not link_elem.has_attr('href'):
                        continue
                    link = f"https://www.kdi.re.kr{link_elem['href']}"
                    date_elem = item.select_one('.date') or item.select_one('.board-date')
                    date = date_elem.text.strip() if date_elem else ""
                    author_elem = item.select_one('.name') or item.select_one('.author')
                    author = author_elem.text.strip() if author_elem else "저자 미상"
                    report_data = {
                        'title': title,
                        'author': author,
                        'date': date,
                        'link': link
                    }
                    reports.append(report_data)
                except Exception:
                    continue
        return pd.DataFrame(reports) if reports else pd.DataFrame()

    def _request_with_retry(self, url):
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    return response
                else:
                    logging.warning(f"HTTP 오류({response.status_code}) - 재시도 {attempt+1}/{self.max_retries}: {url}")
            except Exception as e:
                logging.warning(f"요청 예외 발생 - 재시도 {attempt+1}/{self.max_retries}: {url}, 오류: {e}")
            time.sleep(self.delay)
        return None

    def _select_with_fallback(self, soup, selectors, url):
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logging.info(f"Selector 성공: {selector}, 항목 수: {len(items)}")
                return items
        logging.warning(f"모든 selector 실패: {url}")
        return []
