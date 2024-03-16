import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from time import sleep
from bs4 import BeautifulSoup
from db_conn import get_db_conn
from urllib.parse import urlparse
from scrap_filter import WebScraper;
from scrap_result import DataWebScraper;
from test import Test;

if __name__ == "__main__":
    # Query filters
    options = Options()
    options.add_argument("--headless")
    options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    URL1 = os.getenv("URL1")
    URL2 = os.getenv("URL2")

    db_conn = get_db_conn()

    # # Create the table first
    # WebScraper.create_tables(db_conn)

    # Scrap filters
    # scraper = WebScraper("/home/nicolas/projects/scraper_python/chromedriver-linux64/chromedriver", options)
    # for url in [URL1, URL2]:
    #     html = scraper.get_html(url)
    #     scraper.parse_html(url, html, db_conn)

    # Scrap results
    # resultsScraper = WebScraper("/home/nicolas/projects/scraper_python/chromedriver-linux64/chromedriver", options)
    # for url in [URL2]:
    #     html = resultsScraper.get_html(url)
    #     print(html)
    #     resultsScraper.parse_html(url, html, db_conn)

    # scraper.quit()

    # db_conn.close()
    
    #STEP2: Query Results
    dataScraper = DataWebScraper("/home/nicolas/projects/scraper_python/chromedriver-linux64/chromedriver", options)
    for url in [URL2]:
        html = dataScraper.get_html(url + '?InSel=&InCompet=20230102&InSpec=2&InVille=&InClub=&InDate=&InDatef=&InCat=8&InPhase=0&InVoir=Voir+les+r%C3%A9sultats')
        print(html)
        dataScraper.parse_html(url, html, db_conn)

    Test.printHello();
    print("Done");
