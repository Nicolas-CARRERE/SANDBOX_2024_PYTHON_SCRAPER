import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from time import sleep
from bs4 import BeautifulSoup
from db_conn import get_db_conn
from urllib.parse import urlparse

# This class is used to scrape the website and the filters witch are available
class WebScraper:
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

    # This function create_tables is used to create the tables in the database
    @staticmethod
    def create_tables(db_conn):
        cursor = db_conn.cursor()
        commands = (
            """
            CREATE TABLE IF NOT EXISTS subdomain (
                subdomain_id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS criteria (
                criteria_id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS criteria_value (
                criteria_value_id SERIAL PRIMARY KEY,
                value TEXT NULL,
                text TEXT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS data (
                data_id SERIAL PRIMARY KEY,
                scraped_url TEXT NULL,
                data_html TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS filter (
                filter_id SERIAL PRIMARY KEY,
                subdomain_id INTEGER REFERENCES subdomain(subdomain_id),
                criteria_id INTEGER REFERENCES criteria(criteria_id),
                criteria_value_id INTEGER REFERENCES criteria_value(criteria_value_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS data_filters (
                data_id INTEGER REFERENCES data(data_id),
                filter_id INTEGER REFERENCES filter(filter_id)
            );
            """
        )
        for command in commands:
            cursor.execute(command)
        db_conn.commit()
    
    # This function record_exists is used to check if the record exists in the database
    @staticmethod
    def record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
        cursor = db_conn.cursor()
        query = """
            SELECT EXISTS(
                SELECT 1 FROM filter
                WHERE subdomain_id = %s
                AND criteria_id = %s
                AND criteria_value_id = %s
            )
        """
        cursor.execute(query, (subdomain_id, criteria_id, criteria_value_id))
        return cursor.fetchone()[0]

    # This function get_id is used to get the id of the record in the database
    @staticmethod
    def get_id(db_conn, table_name, column_name, value, text=None):
        cursor = db_conn.cursor()
        if table_name == "criteria_value":
            cursor.execute(f"SELECT {table_name}_id FROM {table_name} WHERE {column_name} = %s AND text = %s", (value, text))
        else:
            cursor.execute(f"SELECT {table_name}_id FROM {table_name} WHERE {column_name} = %s", (value,))
        result = cursor.fetchone()
        if result is None:
            if table_name == "criteria_value":
                cursor.execute(f"INSERT INTO {table_name} ({column_name}, text) VALUES (%s, %s) RETURNING {table_name}_id", (value, text))
            else:
                cursor.execute(f"INSERT INTO {table_name} ({column_name}) VALUES (%s) RETURNING {table_name}_id", (value,))
            result = cursor.fetchone()
            db_conn.commit()
        return result[0]

    # This function parse_html is used to parse the html and save the filters to the database
    @staticmethod
    def parse_html(url, html, db_conn):
        parsed_url = urlparse(url)
        subdomain = parsed_url.hostname.split('.')[0]
        soup = BeautifulSoup(html, 'html.parser')
        selects = soup.find_all('select')
        for select in selects:
            options = select.find_all('option')
            for option in options:
                subdomain_id = WebScraper.get_id(db_conn, "subdomain", "name", subdomain)
                criteria_id = WebScraper.get_id(db_conn, "criteria", "name", select['name'])
                criteria_value_id = WebScraper.get_id(db_conn, "criteria_value", "value", option['value'], option.text)
                if not WebScraper.record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
                    WebScraper.save_to_db(db_conn, subdomain, select['name'], option['value'], option.text)

    # This function save_to_db is used to save the record to the database
    @staticmethod
    def save_to_db(db_conn, subdomain, criteria, criteria_value, option_text):
        cursor = db_conn.cursor()

        subdomain_id = WebScraper.get_id(db_conn, "subdomain", "name", subdomain)
        criteria_id = WebScraper.get_id(db_conn, "criteria", "name", criteria)
        criteria_value_id = WebScraper.get_id(db_conn, "criteria_value", "value", criteria_value, option_text if option_text else '')

        cursor.execute("SELECT * FROM criteria_value WHERE criteria_value_id = %s", (criteria_value_id,))
        result = cursor.fetchone()
        if result is None:
            raise ValueError(f"criteria_value_id {criteria_value_id} does not exist in criteria_value table")
        else:
            if not WebScraper.record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
                cursor.execute("INSERT INTO filter (subdomain_id, criteria_id, criteria_value_id) VALUES (%s, %s, %s)",
                            (subdomain_id, criteria_id, criteria_value_id))
                db_conn.commit()

# Here, we call the WebScraper class            
if __name__ == "__main__":
    options = Options()
    options.add_argument("--headless")
    options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    scraper = WebScraper("/home/nicolas/projects/scraper_python/chromedriver-linux64/chromedriver", options)

    URL1 = os.getenv("URL1")
    URL2 = os.getenv("URL2")

    db_conn = get_db_conn()

    # Create the table first
    WebScraper.create_tables(db_conn)

    for url in [URL1, URL2]:
        html = scraper.get_html(url)
        scraper.parse_html(url, html, db_conn)

    scraper.quit()

    db_conn.close()
