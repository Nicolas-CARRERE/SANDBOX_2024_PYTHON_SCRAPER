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

    def fetch_data_from_url(self, url):
        if url:
            return self.loop.run_until_complete(self.fetch_data(url))
        else:
            return print("No result for this URL.")

    async def fetch_data(self, url):
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
                                date = tr.find('td', class_='L0', align='center').text.strip()
                                team1 = tr.find_all('td', class_='L0')[2].text.strip().split('\n')[0].replace('\xa0', ' ')
                                players = tr.find_all('li')
                                players = [player.text.strip().replace('\xa0', ' ') for player in players]
                                playerA1 = players[0]
                                playerB1 = players[1]
                                team2 = tr.find_all('td', class_='L0')[3].text.strip().split('\n')[0].replace('\xa0', ' ')
                                playerA2 = players[2]
                                playerB2 = players[3]
                                score = tr.find_all('td', class_='L0')[4].text.strip()
                                comment = tr.find_all('td', class_='L0')[5].text.strip()
                                games.append({
                                    'title': title,
                                    'championship': championship,
                                    'date': date,
                                    'team1': team1,
                                    'playerA1': playerA1,
                                    'playerB1': playerB1,
                                    'team2': team2,
                                    'playerA2': playerA2,
                                    'playerB2': playerB2,
                                    'score': score,
                                    'comment': comment,
                                    # 'scraped_url': url,
                                })
                            except IndexError:
                                continue
                except AttributeError:
                    championship = None
                # create an object data that will be used to save the results to the database
                data = {
                    'scraped_url': url,
                    'title': title,
                    'championship': championship
                }

                # scrap games : #, date, team1, playerA1, playerB1, team2, playerA2, playerB2, score, result
                print(games)
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
            CREATE TABLE IF NOT EXISTS data (
                data_id SERIAL PRIMARY KEY,
                scraped_url TEXT NULL,
                data_html TEXT NULL,
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
    def record_exists(db_conn, scraped_url, data_html):
        cursor = db_conn.cursor()
        query = """
            SELECT EXISTS(
                SELECT 1 FROM data
                WHERE scraped_url = %s
                AND data_html = %s
            )
        """
        cursor.execute(query, (scraped_url, str(data_html)))
        return cursor.fetchone()[0]

    # This function parse_html is used to parse the html and save the results to the database
    @staticmethod
    def parse_html(url, html, db_conn):
        soup = html
        try:
            if (soup.find('td', class_='erreur').text):
                print(soup.find('td', class_='erreur').text)
                return None
        except:
            pass
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
        text = soup.get_text()
        # break into lines and remove leading and trailing space on each
        # lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        # chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        # text = '\n'.join(chunk for chunk in chunks if chunk)
        tds = soup.find_
        all('td')

        for td in tds:
            if len(td.text.strip()) > 4:
                print(td.text.strip())
            
            lis = td.find_all('li')
            for li in lis:
                print(li.text.strip()) 

        text = tds
        print(text)
        if not ScrapResults.record_exists(db_conn, url, text):
            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO data (scraped_url, data_html) VALUES (%s, %s)", (url, str(html)))
            db_conn.commit()
            return text
        else:
            return None
