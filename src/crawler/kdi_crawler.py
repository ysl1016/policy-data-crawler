class KDICrawler(ResearchInstituteCrawler):
    def __init__(self):
        super().__init__()
        # ... 기존 코드 ...

    def crawl_reports(self, start_page=1, end_page=10, category='정책연구'):
        """KDI 연구보고서 크롤링 (최신 selector 및 실시간성 강화)"""
        reports = []
        try:
            for page in range(start_page, end_page + 1):
                url = f"{self.base_url}/research/reportList?page={page}&category={category}"
                logging.info(f"KDI 페이지 접근 중: {url}")
                try:
                    response = self.session.get(url, headers=self.headers, timeout=30)
                    if response.status_code != 200:
                        logging.error(f"HTTP 오류: {response.status_code}")
                        continue
                    with open(f"{self.debug_dir}/page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # 최신 구조 반영: 여러 selector fallback
                    selectors = [
                        '.board-list .item',
                        '.board-list-box .item',
                        'tr',
                        '.news-list .item',
                        '.report-list .item'
                    ]
                    report_items = []
                    for selector in selectors:
                        items = soup.select(selector)
                        if items:
                            report_items = items
                            logging.info(f"Selector 성공: {selector}, 항목 수: {len(report_items)}")
                            break
                    if not report_items:
                        logging.warning(f"항목 selector 실패: {url}")
                        continue
                    for item in report_items:
                        try:
                            # 제목 추출
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
                            time.sleep(2)
                        except Exception as e:
                            logging.error(f"보고서 항목 처리 중 오류: {e}")
                    logging.info(f"페이지 {page} 완료")
                    time.sleep(3)
                except Exception as e:
                    logging.error(f"페이지 {page} 처리 중 오류: {e}")
        except Exception as e:
            logging.error(f"KDI 크롤링 중 오류: {e}")
        logging.info(f"KDI 크롤링 완료: {len(reports)}개 보고서")
        return pd.DataFrame(reports) if reports else pd.DataFrame()

    def get_report_detail(self, url):
        """KDI 보고서 상세 페이지 크롤링 (최신 selector 반영)"""
        detail = {}
        try:
            logging.info(f"상세 정보 요청 중: {url}")
            response = self.session.get(url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                logging.error(f"상세 페이지 HTTP 오류: {response.status_code}")
                return detail
            detail_filename = f"{self.debug_dir}/detail_{url.split('/')[-1]}.html"
            with open(detail_filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            # 초록 추출 - 여러 selector fallback
            abstract_selectors = [
                '.report-view-contents',
                '.view-contents',
                '.article-content',
                '.content-area',
                '.summary',
                '.abstract',
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
                '.keywords span',
                '.keyword',
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
                '.file-download a',
                'a[href$=".pdf"]',
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

    def crawl_reports_by_keyword(self, keyword, start_page=1, end_page=3, category='정책연구'):
        """키워드 기반 KDI 연구보고서 실시간 크롤링"""
        import pandas as pd
        from bs4 import BeautifulSoup
        reports = []
        selectors = self.config.get('kdi_selectors', [])
        for page in range(start_page, end_page + 1):
            url = f"https://www.kdi.re.kr/research/reportList?page={page}&category={category}"
            response = self.session.get(url, headers=self.headers, timeout=30)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            report_items = []
            for sel in selectors:
                report_items = soup.select(sel)
                if report_items:
                    break
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
