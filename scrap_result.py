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

# This class is used to scrape the website and the results witch are available
class ScrapResults:
    ''' scrap results from url'''
    # This function __init__ is used to initialize the class
    def __init__(self, url: str):
        self.conf = Conf()
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.session = self._create_session()
        self.loop = asyncio.get_event_loop()
        self.db_conn = get_db_conn()

    def fetch_data_from_url(self, url, combination):
        if url:
            return self.loop.run_until_complete(self.fetch_data(url, combination))
        else:
            return print("No result for this URL.")

    async def fetch_data(self, url, combination):
        page = self.session.get(url, headers=self.headers, allow_redirects=True)
        if page.status_code == 200:
            await asyncio.sleep(random.randint(3, 5))
            page = self.session.get(url, headers=self.headers)
            if page.status_code == 200:
                soup = bs4(page.content, 'html.parser')
                # remove scripts
                for script in soup(["script", "style"]):
                    script.extract()
                # remove   <div id="menu">
                for head in soup.find_all("head"):
                    head.decompose()
                for div in soup.find_all("div", {'id': 'menu'}):
                    div.decompose()
                for form in soup.find_all("form"):
                    form.decompose()
                html = soup.prettify()
                # Écriture de la valeur dans un fichier texte
                # with open("valeur.txt", "w") as file:
                #     file.write(html)

                # get the title
                title = None
                try:
                    h1 = soup.find('h1')
                    if h1:
                        title = h1.text.split('\n')[1].strip()
                except AttributeError as e:
                    title = None

                # get the championship
                championship = None
                games = []
                try:
                    for tr in enumerate(soup.find_all('tr')):
                        index, tr = tr
                        if index == 1:
                            for td in tr.find_all('td'):
                                if td.text:
                                    championship = td.text.split('\n')[1].strip()
                        else:
                            try:
                                if len(tr.find_all('td')) < 6:
                                    continue
                                subdomain_id = self.get_id(self.db_conn, 'subdomain', 'label', combination[0])
                                championship_id = self.get_id(self.db_conn, 'championship', 'value', combination[1])
                                speciality_id = self.get_id(self.db_conn, 'speciality', 'value', combination[2])
                                category_id = self.get_id(self.db_conn, 'category', 'value', combination[3])
                                date = tr.find('td', align='center').text.strip()
                                team1 = tr.find_all('td')[2].text.strip().split('\n')[0].replace('\xa0', ' ')
                                game = tr.find_all('strong')[0].text.strip().replace(' ', '').replace('\t', '')
                                players = tr.find_all('li')
                                players = [player.text.strip().replace('\xa0', ' ') for player in players]
                                playerA1 = players[0]
                                playerB1 = players[1]
                                team2 = tr.find_all('td')[3].text.strip().split('\n')[0].replace('\xa0', ' ')
                                playerA2 = players[2]
                                playerB2 = players[3]
                                score = tr.find_all('td')[4].text.strip()
                                comment = tr.find_all('td')[5].text.strip()
                                games.append({
                                    'subdomain_id': subdomain_id,
                                    'championship_id': championship_id,
                                    'speciality_id': speciality_id,
                                    'category_id': category_id,
                                    'scraped_url': url,
                                    'title': title,
                                    'date': date,
                                    'game': game,
                                    'team1': team1,
                                    'playerA1': playerA1,
                                    'playerB1': playerB1,
                                    'team2': team2,
                                    'playerA2': playerA2,
                                    'playerB2': playerB2,
                                    'score': score,
                                    'comment': comment,
                                })
                                print(f"Scraped game: {game}")
                            except IndexError:
                                continue
                except AttributeError:
                    championship = None
                return games
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
    def create_table(db_conn):
        cursor = db_conn.cursor()
        command = """
        CREATE TABLE IF NOT EXISTS data (
            data_id SERIAL PRIMARY KEY,
            subdomain_id INT NOT NULL,
            championship_id INT NOT NULL,
            speciality_id INT NOT NULL,
            category_id INT NOT NULL,
            scraped_url TEXT NULL,
            title TEXT NULL,
            date TEXT NULL,
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
        cursor.execute(command)
        db_conn.commit()

    # This function record_exists is used to check if the record exists in the database
    @staticmethod
    def record_exists(db_conn, subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2, score, comment):
        cursor = db_conn.cursor()
        query = """
            SELECT EXISTS(
                SELECT 1 FROM data
                WHERE subdomain_id = %s
                AND championship_id = %s
                AND speciality_id = %s
                AND category_id = %s
                AND scraped_url = %s
                AND title = %s
                AND date = %s
                AND game = %s
                AND team1 = %s
                AND playerA1 = %s
                AND playerB1 = %s
                AND team2 = %s
                AND playerA2 = %s
                AND playerB2 = %s
                AND score = %s
                AND comment = %s
            )
        """
        cursor.execute(query, (subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2, score, comment))
        return cursor.fetchone()[0]
    
    # This function get id from an entity according to the label
    @staticmethod
    def get_id(db_conn, table, column, value):
        cursor = db_conn.cursor()
        query = f"""
            SELECT id FROM {table}
            WHERE {column} = %s
        """
        cursor.execute(query, (value,))
        return cursor.fetchone()[0]

    # This function parse_html is used to parse the html and save the results to the database
    @staticmethod
    def save_into_db(db_conn, subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2, score, comment, created_at, updated_at):
        cursor = db_conn.cursor()
        # Check if the record exists
        check_query = """
            SELECT 1 FROM data
            WHERE subdomain_id = %s
            AND championship_id = %s
            AND speciality_id = %s
            AND category_id = %s
            AND scraped_url = %s
            AND title = %s
            AND date = %s
            AND game = %s
            AND team1 = %s
            AND playerA1 = %s
            AND playerB1 = %s
            AND team2 = %s
            AND playerA2 = %s
            AND playerB2 = %s
        """
        cursor.execute(check_query, (subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2))
        exists = cursor.fetchone()

        if exists:
            # If record exists, update it
            update_query = """
                UPDATE data
                SET
                    score = %s,
                    comment = %s,
                    updated_at = %s
                WHERE subdomain_id = %s
                AND championship_id = %s
                AND speciality_id = %s
                AND category_id = %s
                AND scraped_url = %s
                AND title = %s
                AND date = %s
                AND game = %s
                AND team1 = %s
                AND playerA1 = %s
                AND playerB1 = %s
                AND team2 = %s
                AND playerA2 = %s
                AND playerB2 = %s
            """
            cursor.execute(update_query, (score, comment, updated_at, subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2))
        else:
            # If record does not exist, insert it
            insert_query = """
                INSERT INTO data (subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2, score, comment, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (subdomain_id, championship_id, speciality_id, category_id, scraped_url, title, date, game, team1, playerA1, playerB1, team2, playerA2, playerB2, score, comment, created_at, updated_at))

        db_conn.commit()
        return cursor.lastrowid