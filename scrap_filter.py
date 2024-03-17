#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import random
import asyncio
from bs4 import BeautifulSoup as bs4
import requests
from dotenv import load_dotenv
from resources.conf import Conf

import os
import time
import random
import asyncio
from bs4 import BeautifulSoup as bs4
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv
from resources.conf import Conf
from urllib.parse import urlparse
from db_conn import get_db_conn

# This class is used to scrape the website and the filters witch are available
class ScrapFilters:
    ''' scrap filters from url'''
    # This function __init__ is used to initialize the class
    def __init__(self, championship: str):
        self.conf = Conf()
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.session = self._create_session()
        self.loop = asyncio.get_event_loop()

    def fetch_data_from_url(self, championship):
        url = self.conf.championship_list.get(championship)
        if url:
            return self.loop.run_until_complete(self.fetch_data(url))
        else:
            return print("Championship URL not found in the configuration.")

    async def fetch_data(self, url):
        page = self.session.get(url, headers=self.headers, allow_redirects=True)
        if page.status_code == 200:
            await asyncio.sleep(random.randint(3, 5))
            page = self.session.get(url, headers=self.headers)
            if page.status_code == 200:
                html = bs4(page.text, 'html.parser')
                return html
            else:
                print("Failed to retrieve the page after delay. Status code:", page.status_code)
                return None
        else:
            print("Failed to retrieve the initial page. Status code:", page.status_code)
            return None
        
    # This function create_session is used to create a session for the requests library.
    def _create_session(self):
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

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
        soup = html
        selects = soup.find_all('select')
        for select in selects:
            options = select.find_all('option')
            for option in options:
                subdomain_id = ScrapFilters.get_id(db_conn, "subdomain", "name", subdomain)
                criteria_id = ScrapFilters.get_id(db_conn, "criteria", "name", select['name'])
                criteria_value_id = ScrapFilters.get_id(db_conn, "criteria_value", "value", option['value'], option.text)
                if not ScrapFilters.record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
                    ScrapFilters.save_to_db(db_conn, subdomain, select['name'], option['value'], option.text)

    # This function save_to_db is used to save the record to the database
    @staticmethod
    def save_to_db(db_conn, subdomain, criteria, criteria_value, option_text):
        cursor = db_conn.cursor()

        subdomain_id = ScrapFilters.get_id(db_conn, "subdomain", "name", subdomain)
        criteria_id = ScrapFilters.get_id(db_conn, "criteria", "name", criteria)
        criteria_value_id = ScrapFilters.get_id(db_conn, "criteria_value", "value", criteria_value, option_text if option_text else '')

        cursor.execute("SELECT * FROM criteria_value WHERE criteria_value_id = %s", (criteria_value_id,))
        result = cursor.fetchone()
        if result is None:
            raise ValueError(f"criteria_value_id {criteria_value_id} does not exist in criteria_value table")
        else:
            if not ScrapFilters.record_exists(db_conn, subdomain_id, criteria_id, criteria_value_id):
                cursor.execute("INSERT INTO filter (subdomain_id, criteria_id, criteria_value_id) VALUES (%s, %s, %s)",
                            (subdomain_id, criteria_id, criteria_value_id))
                db_conn.commit()
