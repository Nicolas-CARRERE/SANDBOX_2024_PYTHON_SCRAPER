#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random

import requests

from resources.conf import Conf

class ProxiesManager():
    ''' Class for all internal configuration of scrap'''
    def __init__(self,logger):
        self.conf = Conf()
        self.logger = logger
    
    def _get_proxies_from_api(self, endpoint, proxy_error, proxy_error_status_code):
        response = requests.get(
            f"{self.conf.api_endpoint}{endpoint}",
            headers={'x-api-key': self.conf.api_key},
            verify=False,
        )
        if response.status_code == 200:
            json_resp = json.loads(response.text)
            if json_resp['status'] == 'ok':
                return json_resp['proxies']
            self.logger.error(proxy_error)
        else:
            self.logger.error(proxy_error_status_code)
        return None

    def get_semi_dedicated_proxies_list(self):
        try:
            return self._get_proxies_from_api(
                '/semi_dedicated_proxies/',
                "in ProxyManager().get_semi_dedicated_proxies_list() : Proxies API response is not ok",
                "in ProxyManager().get_semi_dedicated_proxies_list() : Proxies API resp status_code is not 200",
            )
        except Exception as error:
            self.logger.critical(f"in ProxyManager().get_semi_dedicated_proxies_list() : {error}")
            return None


    def get_random_proxy_from_a_list(self, proxies_list=None):
        random_proxy = None
        if proxies_list is not None:
            random_proxy = random.choice(proxies_list)        
            return {
                "http"  : f"http://{random_proxy['user']}:{random_proxy['password']}@{random_proxy['ip']}:{random_proxy['port']}",
                "https" : f"http://{random_proxy['user']}:{random_proxy['password']}@{random_proxy['ip']}:{random_proxy['port']}",
            }
        return None

    def get_residential_proxies(self):        
        try:
            return self._get_proxies_from_api(
                '/residential_proxies/',
                "in ProxyManager().residential_proxies() : Proxies API response is not ok",
                "in ProxyManager().residential_proxies() : Proxies API resp status_code is not 200",
            )
        except Exception as error:
            self.logger.critical(f"in ProxyManager().residential_proxies() : {error}")
            return None
