# create a script based on scrap_filter.py
# to iterate on the differents filter to get the results and store them in DB
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from time import sleep
from bs4 import BeautifulSoup
from db_conn import get_db_conn
from urllib.parse import urlparse

# This class is used to scrape the website and the filters witch are available
class DataWebScraper:
    # This function __init__ is used to initialize the class
    def __init__(self, driver_path, browser_options):
        self.driver = self.setup_driver(driver_path, browser_options)

    # This function setup_driver is used to setup the driver of the browser
    @staticmethod
    def setup_driver(driver_path, browser_options):
        service = Service(driver_path)
        service.start()
        return webdriver.Chrome(service=service, options=browser_options)

    # This function quit is used to quit the driver of the browser
    def quit(self):
        self.driver.quit()

    # This function get_html is used to get the html of the website
    # It is used to get the html of the website and the filters witch are available
    # By calling get twice we ensure that the page is fully loaded before we start scraping
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

    # This function record_exists is used to check if the record exists in the database
    @staticmethod
    def record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
        cursor = db_conn.cursor()
        query = """
            SELECT EXISTS(
                SELECT 1 FROM data
                WHERE scraped_url = %s
                AND data_html = %s
                AND updated_at = %s
            )
        """
        cursor.execute(query, (subdomain_id, criteria_id, criteria_value_id))
        return cursor.fetchone()[0]

    # This function parse_html is used to parse the HTML and save the filters to the database
    @staticmethod
    def parse_html(url, html, db_conn):
        soup = BeautifulSoup(html, 'html.parser')
        tds = soup.find_all('td')
        
        for td in tds:
            if len(td.text.strip()) > 4:
                print(td.text)
            
            lis = td.find_all('li')
            for li in lis:
                print(li.text.strip())                    
                # DataWebScraper.save_to_db(db_conn, subdomain, select['name'], option['value'], option.text)   

    # This function save_to_db is used to save the record to the database
    # @staticmethod
    # def save_to_db(db_conn, subdomain, criteria, criteria_value, option_text):
    #     cursor = db_conn.cursor()

    #     scraped_url = 
    #     data_html = DataWebScraper.get_id(db_conn, "criteria", "name", criteria)
    #     created_at = datetime.now()
    #     updated_at = datetime.now()

    #     cursor.execute("SELECT * FROM criteria_value WHERE criteria_value_id = %s", (criteria_value_id,))
    #     result = cursor.fetchone()
    #     if result is None:
    #         raise ValueError(f"criteria_value_id {criteria_value_id} does not exist in criteria_value table")
    #     else:
    #         if not DataWebScraper.record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
    #             cursor.execute("INSERT INTO filter (subdomain_id, criteria_id, criteria_value_id) VALUES (%s, %s, %s)",
    #                         (subdomain_id, criteria_id, criteria_value_id))
    #             db_conn.commit()

