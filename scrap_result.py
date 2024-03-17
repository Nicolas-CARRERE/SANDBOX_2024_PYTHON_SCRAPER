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

class ScrapData:
    def __init__(self, championship):
        self.conf = Conf()
        url = self.conf.championship_list.get(championship)
        if url:
            headers = {'User-Agent': 'Mozilla/5.0'}
            session = self._create_session()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.fetch_data(session, url, headers))
        else:
            print("Championship URL not found in the configuration.")

    # This function fetch_data is used to fetch the data from the website
    async def fetch_data(self, session, url, headers):
        page = session.get(url, headers=headers, allow_redirects=True)
        if page.status_code == 200:
            await asyncio.sleep(random.randint(3, 5))
            page = session.get(url, headers=headers)
            if page.status_code == 200:
                html = bs4(page.text, 'html.parser')
                selects = html.find_all('select')
            else:
                print("Failed to retrieve the page after delay. Status code:", page.status_code)
        else:
            print("Failed to retrieve the initial page. Status code:", page.status_code)

    # This function create_session is used to create a session for the requests library.
    def _create_session(self):
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

if __name__ == "__main__":
    ScrapData('basque_union')