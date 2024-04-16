#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
                id SERIAL PRIMARY KEY,
                label VARCHAR(100) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS championship (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                label VARCHAR(255) NOT NULL,
                subdomain_id INT
            )
            """,            
            """
            CREATE TABLE IF NOT EXISTS speciality (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                label VARCHAR(255) NOT NULL,
                subdomain_id INT
            )
            """,            
            """
            CREATE TABLE IF NOT EXISTS city (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                label VARCHAR(255) NOT NULL,
                subdomain_id INT
            )
            """,            
            """
            CREATE TABLE IF NOT EXISTS club (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                label VARCHAR(255) NOT NULL,
                subdomain_id INT
            )
            """,            
            """
            CREATE TABLE IF NOT EXISTS category (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                label VARCHAR(255) NOT NULL,
                subdomain_id INT
            )
            """,            
            """
            CREATE TABLE IF NOT EXISTS phase (
                id SERIAL PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                label VARCHAR(255) NOT NULL,
                subdomain_id INT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS data (
                id SERIAL PRIMARY KEY,
                subdomain_id INT,
                championship_id INT,
                speciality_id INT,
                category_id INT,
                scraped_url TEXT NULL,
                title VARCHAR(255) NULL,
                date DATE NULL,
                game TEXT NULL,
                team1 TEXT NULL,
                playerA1 TEXT NULL,
                playerB1 TEXT NULL,
                team2 TEXT NULL,
                playerA2 TEXT NULL,
                playerB2 TEXT NULL,
                score TEXT NULL,
                comment TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for command in commands:
            cursor.execute(command)
        db_conn.commit()
    
    # This function record_exists is used to check if the record exists in the database
    @staticmethod
    def record_exists(db_conn, subdomain_id, championship_id, speiality_id, category_id):
        cursor = db_conn.cursor()
        query = """
            SELECT EXISTS(
                SELECT 1 FROM data
                WHERE subdomain_id = %s
                AND championship_id = %s
                AND speciality_id = %s
                AND category_id = %s
            )
        """
        cursor.execute(query, (subdomain_id, championship_id, speiality_id, category_id))
        return cursor.fetchone()[0]

    # This function get_id is used to get the id of the record in the database
    @staticmethod
    def get_id(db_conn, table_name, column_name, value, text=None):
        # print(f"table_name: {table_name}, column_name: {column_name}, value: {value}, text: {text}")
        criteria_table_mapping = {
            "InCompet": "championship",
            "InSpec": "speciality",
            "InVille": "city",
            "InClub": "club",
            "InCat": "category",
            "InPhase": "phase",
            "InComite": None
        }
        if table_name == "criteria":
            table_name = criteria_table_mapping.get(value)
            if table_name is None:
                return

        cursor = db_conn.cursor()
        if table_name == "data":
            cursor.execute(f"SELECT id FROM {table_name} WHERE {column_name} = %s AND text = %s", (value, text))
        else:
            cursor.execute(f"SELECT id FROM {table_name} WHERE {column_name} = %s", (value,))
        result = cursor.fetchone()
        if result is None:
            if table_name == "data":
                cursor.execute(f"INSERT INTO {table_name} ({column_name}, text) VALUES (%s, %s) RETURNING id", (value, text))
            # else:
            #     cursor.execute(f"INSERT INTO {table_name} ({column_name}) VALUES (%s) RETURNING id", (value,))
            # result = cursor.fetchone()
            db_conn.commit()
        return result[0] if result else None

    # This function parse_html is used to parse the html and save the filters to the database
    @staticmethod
    def parse_html(url, html, db_conn):
        parsed_url = urlparse(url)
        subdomain = parsed_url.hostname.split('.')[0]
        soup = html
        selects = soup.find_all('select')
        for select in selects:
            options = [option for option in select.find_all('option') if not any(x in option.text.lower() for x in ["*", "tous", "toutes"]) and option.text.strip()]
            for option in options:
                # Now the get_id function will insert the data into the correct table based on the criteria
                id = ScrapFilters.get_id(db_conn, "criteria", select['name'], option['value'], option.text)
                # if no id save the record in the database
                if not id:
                    ScrapFilters.save_to_db(db_conn, subdomain, select['name'], option['value'], option.text)

    # This function save_to_db is used to save the record to the database
    @staticmethod
    def save_to_db(db_conn, subdomain, criteria, criteria_value, option_text):
        cursor = db_conn.cursor()

        subdomain_id = ScrapFilters.get_id(db_conn, "subdomain", "label", subdomain)

        # map criteria to specific table
        criteria_table_mapping = {
            "InCompet": "championship",
            "InSpec": "speciality",
            "InVille": "city",
            "InClub": "club",
            "InCat": "category",
            "InPhase": "phase",
            "InComite": None
        }

        table_name = criteria_table_mapping.get(criteria)
        if table_name is None:
            return

        cursor.execute(f"SELECT id FROM {table_name} WHERE value = %s", (criteria_value,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO {table_name} (value, label, subdomain_id) VALUES (%s, %s, %s) RETURNING id",
                        (criteria_value, option_text, subdomain_id))
            db_conn.commit()
