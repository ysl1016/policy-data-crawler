from src.crawler.kdi_crawler import KDICrawler
from src.crawler.bok_crawler import BOKCrawler
import pandas as pd

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        keyword = request.form.get('keyword', '')
        start_page = 1
        end_page = 2  # 실시간 크롤링 범위(조정 가능)
        # 실시간 크롤링: KDI + BOK
        kdi_crawler = KDICrawler()
        bok_crawler = BOKCrawler()
        df_kdi = kdi_crawler.crawl_reports_by_keyword(keyword, start_page, end_page)
        df_bok = bok_crawler.crawl_reports_by_keyword(keyword, start_page, end_page)
        results_df = pd.concat([df_kdi, df_bok], ignore_index=True)
        results_df.to_csv('search_results.csv', index=False, encoding='utf-8-sig')  # CSV 저장
        results = results_df.to_dict(orient='records')
    return render_template('index.html', results=results) 
