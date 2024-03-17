# -*- coding: utf-8 -*-

import os

from datetime import datetime
import requests
import re
import json
from time import sleep
from db_conn import get_db_conn
from resources.conf import Conf
from scrap_filter import ScrapFilters
from scrap_result import ScrapData

class Scrap:
    def __init__(self):
        self.conf = Conf()

    def main(self):
        print("Start")
        
        # STEP 1: Scrap Filters
        db_conn = get_db_conn()
        ScrapFilters.create_tables(db_conn)
        
        scraper = Scrap()
        for championship in scraper.conf.championship_list:
            print("Scrapping championship: " + championship)
            # STEP 1: Scrap Filters
            filter = ScrapFilters(championship)
            html = filter.fetch_data_from_url(championship)
            filter.create_tables(db_conn)
            filter.parse_html(self.conf.championship_list.get(championship), html, db_conn)
            print("Scrapping championship {} done".format(championship))

if __name__ == "__main__":
    scraper = Scrap()
    scraper.main()
