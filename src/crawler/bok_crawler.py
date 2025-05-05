import time
import logging
import pandas as pd
from bs4 import BeautifulSoup
import os

class BOKCrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        self.selectors = self.config.get('bok_selectors', [])
        self.max_retries = 3
        self.delay = 2

    def crawl_reports(self, start_page=1, end_page=10, category='research'):
        """한국은행 연구보고서 크롤링 (실시간성 및 신뢰성 강화)"""
        reports = []
        existing_links = set()
        if os.path.exists('bok_reports.csv'):
            df_existing = pd.read_csv('bok_reports.csv')
            existing_links = set(df_existing['link'].tolist())
        for page in range(start_page, end_page + 1):
            url = f"https://www.bok.or.kr/portal/bbs/B0000217/list.do?menuNo=200761&pageIndex={page}"
            response = self._request_with_retry(url)
            if not response:
                logging.error(f"페이지 요청 실패: {url}")
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            report_items = self._select_with_fallback(soup, self.selectors, url)
            for item in report_items:
                try:
                    cols = item.select('td')
                    title_elem = None
                    for col in cols:
                        a_tag = col.select_one('a')
                        if a_tag:
                            title_elem = a_tag
                            break
                    if not title_elem:
                        self.failed_items.append({'page': page, 'reason': '제목 요소 없음'})
                        self.fail_count += 1
                        continue
                    title = title_elem.text.strip()
                    link = f"https://www.bok.or.kr{title_elem['href']}" if title_elem.has_attr('href') else ""
                    if not title or not link:
                        self.failed_items.append({'page': page, 'reason': '필수 필드 누락'})
                        self.fail_count += 1
                        continue
                    if link in existing_links:
                        continue
                    # 날짜 추출
                    date = ""
                    for col in reversed(cols):
                        date_text = col.text.strip()
                        if len(date_text) >= 8 and (date_text.count('.') == 2 or date_text.count('-') == 2):
                            date = date_text
                            break
                    report_data = {
                        'title': title,
                        'date': date,
                        'link': link
                    }
                    reports.append(report_data)
                    self.success_count += 1
                    logging.info(f"보고서 크롤링 성공: {title}")
                except Exception as e:
                    self.failed_items.append({'page': page, 'reason': str(e)})
                    self.fail_count += 1
            logging.info(f"페이지 {page} 완료")
            time.sleep(self.delay)
        self.save_failed_items('bok_failed_items.json')
        self.report_stats()
        logging.info(f"BOK 크롤링 완료: {len(reports)}개 보고서")
        return pd.DataFrame(reports) if reports else pd.DataFrame()

    def crawl_reports_by_keyword(self, keyword, start_page=1, end_page=3, category='research'):
        """키워드 기반 BOK 연구보고서 실시간 크롤링 (신뢰성 강화)"""
        reports = []
        for page in range(start_page, end_page + 1):
            url = f"https://www.bok.or.kr/portal/bbs/B0000217/list.do?menuNo=200761&pageIndex={page}"
            response = self._request_with_retry(url)
            if not response:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            report_items = self._select_with_fallback(soup, self.selectors, url)
            for item in report_items:
                try:
                    cols = item.select('td')
                    title_elem = None
                    for col in cols:
                        a_tag = col.select_one('a')
                        if a_tag:
                            title_elem = a_tag
                            break
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    if keyword not in title:
                        continue
                    link = f"https://www.bok.or.kr{title_elem['href']}" if title_elem.has_attr('href') else ""
                    date = ""
                    for col in reversed(cols):
                        date_text = col.text.strip()
                        if len(date_text) >= 8 and (date_text.count('.') == 2 or date_text.count('-') == 2):
                            date = date_text
                            break
                    report_data = {
                        'title': title,
                        'date': date,
                        'link': link
                    }
                    reports.append(report_data)
                except Exception:
                    continue
        logging.info(f"BOK 키워드 크롤링 완료: {len(reports)}개 보고서")
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
