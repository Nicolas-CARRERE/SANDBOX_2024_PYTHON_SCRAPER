# -*- coding: utf-8 -*-

import os

from datetime import datetime
import requests
import re
import json
import argparse
from time import sleep
from db_conn import get_db_conn
from resources.conf import Conf
from scrap_filter import ScrapFilters
from scrap_result import ScrapResults

parser = argparse.ArgumentParser()
parser.add_argument("--step1", help="Specify whether to execute Step 1 (Scrap Filters)", action="store_true")
args = parser.parse_args()

class Scrap:
    def __init__(self):
        self.conf = Conf()
        parser = argparse.ArgumentParser()
        parser.add_argument("--step1", help="Specify whether to execute Step 1 (Scrap Filters)", action="store_true")
        args = parser.parse_args()
        self.step1 = args.step1
        
    def scrape_filters(self, db_conn):
        for championship in self.conf.championship_list:
            print(f"Scrapping championship: {championship}")
            filter_scraper = ScrapFilters(championship)
            html = filter_scraper.fetch_data_from_url(championship)
            filter_scraper.create_tables(db_conn)
            filter_scraper.parse_html(self.conf.championship_list.get(championship), html, db_conn)
            print(f"Scrapping championship {championship} done")

    @staticmethod
    def fetch_distinct_values(cursor, table, column):
        cursor.execute(f"""
            SELECT DISTINCT {column} 
            FROM {table}
        """)
        return [item[0] for item in cursor.fetchall()]

    def generate_results_url(self, comb):
        url = f'https://{comb[0]}.euskalpilota.fr/resultats.php?'
        url += f'InCompet={comb[1]}&InSpec={comb[2]}&InCat={comb[3]}&InPhase=&InSel=&InVille=&InClub=&InDate=&InDatef=&InVoir=Voir+les+r%C3%A9sultats'
        return url

    def generate_combinations(self, db_conn):
        cursor = db_conn.cursor()
        
        # Fetch distinct values
        subdomains = self.fetch_distinct_values(cursor, 'subdomain', 'label')
        championship = self.fetch_distinct_values(cursor, 'championship', 'value')
        speciality = self.fetch_distinct_values(cursor, 'speciality', 'value')
        category = self.fetch_distinct_values(cursor, 'category', 'value')

        # Generate all possible combinations of filters using list comprehension
        combinations = [(subdomain, champ, spec, cat) for subdomain in subdomains for champ in championship for spec in speciality for cat in category]

        # to generate all possible combinations of filters
        # the table championship has a subdomain_id value, same thing for the tables speciality and category
        # so we need to get the id of the subdomain, championship, speciality and category
        # to return only valid combinations
        valid_combinations = []
        for comb in combinations:
            subdomain_id = ScrapFilters.get_id(db_conn, 'subdomain', 'label', comb[0])
            championship_id = ScrapFilters.get_id(db_conn, 'championship', 'subdomain_id', subdomain_id)
            speciality_id = ScrapFilters.get_id(db_conn, 'speciality', 'subdomain_id', subdomain_id)
            category_id = ScrapFilters.get_id(db_conn, 'category', 'subdomain_id', subdomain_id)
            if subdomain_id and championship_id and speciality_id and category_id:
                valid_combinations.append((comb[0], comb[1], comb[2], comb[3]))

        return valid_combinations

    def generate_urls(self, combinations):
        urls = []
        for comb in combinations:
            print(f"Combination: {comb}")
            url = f'https://{comb[0]}.euskalpilota.fr/resultats.php?'
            url += f'InCompet={comb[1]}&InSpec={comb[2]}&InCat={comb[3]}&InPhase=&InSel=&InVille=&InClub=&InDate=&InDatef=&InVoir=Voir+les+r%C3%A9sultats'
            urls.append(url)
        return urls

    def scrape_data(self, urls, combinations, db_conn):
            print("Scraping data")
            for index, url in enumerate(urls):
                try:
                    result_scraper = ScrapResults(url)
                    result_scraper.create_table(db_conn)
                    games = result_scraper.fetch_data_from_url(url, combinations[index])
                    for game in games:
                        print(f"Game: {game}")
                        if not result_scraper.complete_record_exists(db_conn, game['subdomain_id'], game['championship_id'], game['speciality_id'], game['category_id'], game['scraped_url'], game['title'], game['date'], game['game'], game['team1'], game['playerA1'], game['playerB1'], game['team2'], game['playerA2'], game['playerB2'], game['score'], game['comment']):
                            print(f"Saving game: {game}")
                            result_scraper.save_into_db(db_conn,
                                                        game['subdomain_id'],
                                                        game['championship_id'],
                                                        game['speciality_id'],
                                                        game['category_id'],
                                                        game['scraped_url'],
                                                        game['title'],
                                                        game['date'],
                                                        game['game'],
                                                        game['team1'],
                                                        game['playerA1'],
                                                        game['playerB1'],
                                                        game['team2'],
                                                        game['playerA2'],
                                                        game['playerB2'],
                                                        game['score'],
                                                        game['comment'],
                                                        datetime.now().strftime('%Y-%m-%d'),
                                                        datetime.now().strftime('%Y-%m-%d'))
                            sleep(1)
                            print(f"Scrapping championship {url} done")
                except AttributeError as e:
                    print(f"Error while scrapping championship {url}")
                    print(e)

    def main(self):
        print("Start")

        db_conn = get_db_conn()
        print("DB connection established")

        if self.step1:
            ScrapFilters.create_tables(db_conn)
            self.scrape_filters(db_conn)

        print("generate_urls")
        combinations = self.generate_combinations(db_conn)
        urls = self.generate_urls(combinations)
        self.scrape_data(urls, combinations, db_conn)

        db_conn.close()
        print("End")

if __name__ == "__main__":
    scraper = Scrap()
    scraper.main()