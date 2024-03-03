import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from time import sleep
from bs4 import BeautifulSoup
from db_conn import get_db_conn
from urllib.parse import urlparse


class WebScraper:
    def __init__(self, driver_path, browser_options):
        self.driver = self.setup_driver(driver_path, browser_options)

    @staticmethod
    def setup_driver(driver_path, browser_options):
        service = Service(driver_path)
        service.start()
        return webdriver.Chrome(service=service, options=browser_options)

    def quit(self):
        self.driver.quit()

    def get_html(self, url):
        try:
            self.driver.get(url)
            sleep(2)
            self.driver.get(url)
            sleep(2)
            return self.driver.page_source
        except Exception as e:
            print("An error occurred while getting HTML:", str(e))
            return None

    @staticmethod
    def parse_html(url, html, db_conn):
        parsed_url = urlparse(url)
        subdomain = parsed_url.hostname.split('.')[0]
        soup = BeautifulSoup(html, 'html.parser')
        selects = soup.find_all('select')
        for select in selects:
            options = select.find_all('option')
            for option in options:
                WebScraper.save_to_db(db_conn, subdomain, select['name'], option['value'], option.text)
                # print(subdomain + "Select value:", select['name'], " / Value:", option['value'], "Text:", option.text)

    @staticmethod
    def save_to_db(db_conn, subdomain, select_name, option_value, option_text):
        cursor = db_conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data (
                subdomain text,
                select_name text,
                option_value text,
                option_text text
            )
        """)

        cursor.execute("INSERT INTO data (subdomain, select_name, option_value, option_text) VALUES (%s, %s, %s, %s)",
                    (subdomain, select_name, option_value, option_text))
        
        db_conn.commit()

if __name__ == "__main__":
    options = Options()
    options.add_argument("--headless")
    options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    scraper = WebScraper("/home/nicolas/projects/scraper_python/chromedriver-linux64/chromedriver", options)

    URL1 = os.getenv("URL1")
    URL2 = os.getenv("URL2")

    db_conn = get_db_conn()

    for url in [URL1, URL2]:
        html = scraper.get_html(url)
        scraper.parse_html(url, html, db_conn)

    scraper.quit()

    db_conn.close()
