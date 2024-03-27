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

    def generate_results_url(self, championship, championship_filters):
            base_url = self.conf.championship_list.get(championship)
            query_params = {
                "InSel": "",
                "InCompet": championship_filters.get("InCompet"),
                "InSpec": championship_filters.get("InSpec"),
                "InCat": championship_filters.get("InCat")
                # Ajoutez d'autres paramètres en fonction des filtres récupérés
            }
            url = base_url + "?" + "&".join([f"{key}={value}" for key, value in query_params.items()])
            return url
    
    def main(self):
        print("Start")
        
        # Connexion à la base de données
        db_conn = get_db_conn()
        
        if args.step1:
            # STEP 1: Scrap Filters
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

        # STEP 2: Scrap Results
        cursor = db_conn.cursor()

        # Correction du code SQL en utilisant l'alias de table "s" au lieu de "subdomain"
        cursor.execute("""
            SELECT 
                DISTINCT s.name 
            FROM public.filter
            JOIN public.subdomain s ON filter.subdomain_id = s.subdomain_id  
            WHERE 1 = 1;
        """)
        subdomains = [sub[0] for sub in cursor.fetchall()]

        cursor.execute("""
            SELECT 
                public.criteria_value.value 
            FROM public.filter
            JOIN public.criteria_value ON filter.criteria_value_id = criteria_value.criteria_value_id
            join public.criteria c on filter.criteria_id = c.criteria_id  
            WHERE c.name IN ('InCompet');
        """)
        compets = [comp[0] for comp in cursor.fetchall()]
        
        cursor.execute("""
            SELECT 
                public.criteria_value.value 
            FROM public.filter
            JOIN public.criteria_value ON filter.criteria_value_id = criteria_value.criteria_value_id
            join public.criteria c on filter.criteria_id = c.criteria_id  
            WHERE c.name IN ('InSpec');
        """)
        specs = [spec[0] for spec in cursor.fetchall()]

        cursor.execute("""
            SELECT 
                public.criteria_value.value 
            FROM public.filter
            JOIN public.criteria_value ON filter.criteria_value_id = criteria_value.criteria_value_id
            join public.criteria c on filter.criteria_id = c.criteria_id  
            WHERE c.name IN ('InCat');
        """)
        cats = [cat[0] for cat in cursor.fetchall()]

        # cursor.execute("""
        #     SELECT 
        #         public.criteria_value.value 
        #     FROM public.filter
        #     JOIN public.criteria_value ON filter.criteria_value_id = criteria_value.criteria_value_id
        #     join public.criteria c on filter.criteria_id = c.criteria_id  
        #     WHERE c.name IN ('InPhase');
        # """)
        # phases = [phase[0] for phase in cursor.fetchall()]
        phases = [0]

        # Générer toutes les combinaisons possibles des filtres
        combinations = [(subdomain, compet, spec, cat, phase) for subdomain in subdomains for compet in compets for spec in specs for cat in cats for phase in phases]

        # Créer les URLs avec les combinaisons de filtres
        urls = []
        # for comb in combinations:
        #     url = f'https://{comb[0]}.euskalpilota.fr/resultats.php?'
        #     url += f'InCompet={comb[1]}&InSpec={comb[2]}&InCat={comb[3]}&InPhase={comb[4]}&InSel=&InVille=&InClub=&InDate=&InDatef=&InVoir=Voir+les+r%C3%A9sultats'
        #     urls.append(url)
        urls.append('https://ub.euskalpilota.fr/resultats.php?InSel=&InCompet=20240102&InSpec=2&InVille=&InClub=&InDate=&InDatef=&InCat=8&InPhase=0&InVoir=Voir+les+r%C3%A9sultats')
        # Afficher les URLs générées
        for url in urls:
            # url = 'https://ctpb.euskalpilota.fr/resultats.php?InSel=&InCompet=20230102&InSpec=2&InVille=&InClub=&InDate=&InDatef=&InCat=8&InPhase=0&InVoir=Voir+les+r%C3%A9sultats'
            # print(url)
            # Récupérer les données de la page
            try:
                result_scraper = ScrapResults(url)
                result_scraper.create_table(db_conn)
                print("Scrapping championship: " + url)
                games = result_scraper.fetch_data_from_url(url)
                print(games)
                for game in games:
                    if result_scraper.record_exists(
                        db_conn,
                        game['scraped_url'],
                        game['title'],
                        game['championship'],
                        game['date'],
                        game['game'],
                        game['team1'],
                        game['playerA1'],
                        game['playerB1'],
                        game['team2'],
                        game['playerA2'],
                        game['playerB2'],
                        game['score'],
                        game['comment']
                    ):
                        continue
                    else:
                        result_scraper.save_into_db(
                            db_conn,
                            game['scraped_url'],
                            game['title'],
                            game['championship'],
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
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
                        sleep(1)
                        print(
                            game['scraped_url'],
                            game['title'],
                            game['championship'],
                            game['date'],
                            game['game'],
                            game['team1'],
                            game['playerA1'],
                            game['playerB1'],
                            game['team2'],
                            game['playerA2'],
                            game['playerB2'],
                            game['score'],
                            game['comment']
                        )
                print("Scrapping championship {} done".format(url))
            except AttributeError as e:
                print("Error while scrapping championship {}".format(url))
                print(e)
                continue

        db_conn.close()
        print("End")

if __name__ == "__main__":
    scraper = Scrap()
    scraper.main()
