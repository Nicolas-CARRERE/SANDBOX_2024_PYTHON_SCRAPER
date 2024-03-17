#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json
import random

import requests
from fake_headers import Headers
from fake_useragent import UserAgent
import asyncio

from resources.proxies_manager import ProxiesManager

class Utils():
    ''' Class for all internal function of scrap'''

    def __init__(self,conf,env,logs_filename,logger):
        self.env = env
        self.conf = conf
        self.logs_filename = logs_filename
        self.proxies_manager =ProxiesManager(logger)
        self.residential_proxies = self.proxies_manager.get_residential_proxies()
        self.logger = logger
        
    # def terminate_scrap(self):
    #     if self.env == 'prod':
    #         requests.post(f"{self.conf.api_endpoint}/treat_log_file_from_scrap/", 
    #                         headers={'x-api-key': self.conf.api_key, 'x-scrap-key': self.conf.scrap_key}, 
    #                         files={'data': (f"{self.conf.local_logs_path}{self.logs_filename}", open(f"{self.conf.local_logs_path}{self.logs_filename}"))})
    

    def send_ads_to_treat(self,ads,start_time):
        try:
            datas = {
                'source': self.conf.scrap_infos['source'],
                'department': self.conf.scrap_infos['department'],
                'ads_count': len(ads),
                'ads_package': ads,
                'script_duration': str(datetime.now() - start_time)
            }
            self.logger.info(f'il y à {len(ads)} ads to send')
            datas = json.dumps(datas, default=str)
            
            # with open('data.json','a') as f:
            #     f.write(datas)
            response = requests.post(f"{self.conf.api_endpoint}/treat_ads_from_scrapping/", headers={'x-api-key': self.conf.api_key}, data=datas, verify=False)

        except Exception as error:
            self.logger.error(f" in send_ads_to_treat() : {error}")


    def _get_value_from_json_path(self,response, path):
        self.response = response
        try:
            for item in path:
                self.response = self.response[item]
        except Exception as error:
            self.logger.warning(f'No value for path : {path} in responce {self.response}')
            return None
        return self.response

    def get_random_header(self,host=None,Referer=None,Fake_user=True,dict_key_value={}):

        random_header = Headers(headers=False).generate()

        if host:
            self.logger.info(host)
            random_header['Host'] = host
        if Referer:
            random_header['Referer'] = Referer
        if Fake_user:
            ua = UserAgent(verify_ssl=False).random
            random_header['User-Agent'] = '\''+ua+'\''
        for key ,value in dict_key_value.items():
            random_header[key] = value
        return random_header


    def get_resp_request(
                        self,
                        url,
                        methode='GET',
                        header={
                                'fake_header': True,
                                'header':{  'host':None,
                                            'referer':None,
                                            'fake_user':True}
                                },
                        dict_key_value={},
                        timeout=10,
                        exclud_str_in_html=[],
                        params=None,
                        data=None,
                        json=None,
                        add_value_in_header=None,
                        semi_dedicated_proxies_list=None):
        ''' 
            header : dict :
                {
                    'fake_header': Bool : if have fake_header
                    'header':   case 1 : { 'host': value host : default None
                                        'referer': value referer : default None
                                        'fake_user': bool : if have fake user : default True
                                        }
                                case 2 : Real header
                }
            add_value_in_header : dict : default None
                {
                    name_of_key_in_header : function take just proxies in arg
                }
            '''
       
        self.logger.info(f'Start to get_resp_request')
        try:
            for count in range(1, 6):
                try:
                    self.logger.info(f' -> Try to connect n°{count} :')

                    proxies = None
                    if count < 5:
                        proxies = self.residential_proxies
                    elif count == 5 and semi_dedicated_proxies_list:
                        self.logger.warning('already 4 attempts with residential proxy -> try with semi dedicated proxies')
                        proxies = self.proxies_manager.get_random_proxy_from_a_list(proxies_list=semi_dedicated_proxies_list)

                    if proxies:
                        self.logger.info(f'    -> proxies : {proxies}')
                        headers =None
                        if 'fake_header' in header.keys() and header['fake_header']:
                            headers = self.get_random_header(host=header['header']['host'],Referer= header['header']['referer'],Fake_user=header['header']['fake_user'],dict_key_value=dict_key_value)
                        elif 'fake_header' in header.keys() and not header['fake_header']:
                            headers = header['header']
                        else:
                            self.logger.warning('miss argument fake_header in param of fonction')
                            return None

                        if add_value_in_header:
                            for key ,value in add_value_in_header.items():
                                headers[key] =value(proxies)
                        self.logger.info(f'    -> headers : {headers}')
                        self.logger.info(f'    -> url : {url}')

                        try:
                            html_resp=None
                            if methode == 'GET':
                                html_resp = requests.get(url,
                                                        headers=headers,
                                                        proxies=proxies,
                                                        timeout=timeout,verify=False,
                                                        params=params)

                            elif methode =='POST':
                                html_resp = requests.post(url, 
                                                        headers=headers, 
                                                        proxies=proxies,
                                                        timeout=timeout,verify=False,
                                                        params=params,
                                                        data=data,
                                                        json=json)

                            if html_resp.status_code == 200 and True not in [
                                str_check in html_resp.text
                                for str_check in exclud_str_in_html
                            ]:
                                self.logger.info('    -> Succes to connect')
                                return html_resp
                            else: 
                                self.logger.warning(f'    -> Echec to connect wong statue or wrong html, status_code is : {html_resp.status_code}')
                        except Exception as error:
                            self.logger.error(f'in try request : {error}')
                    else:
                        self.logger.error('No proxy found -> return None')
                        return None
                except Exception as error:
                        self.logger.error(f" -> in param for request in get_resp_request : {error}")

        except Exception as error:
            self.logger.error(f'in get_resp_request : {error}')
            return None

    async def get_resp_request_async(
                        self,
                        url,
                        methode='GET',
                        header={
                                'fake_header': True,
                                'header':{  'host':None,
                                            'referer':None,
                                            'fake_user':True}
                                },
                        dict_key_value={},
                        timeout=10,
                        exclud_str_in_html=[],
                        params=None,
                        data=None,
                        json=None,
                        add_value_in_header=None,
                        ssl=False,
                        session=None,
                        async_log=False,
                        async_log_list=[],
                        semi_dedicated_proxies_list=None
                      ):
        ''' 
            header : dict :
                {
                    'fake_header': Bool : if have fake_header
                    'header':   case 1 : { 'host': value host : default None
                                        'referer': value referer : default None
                                        'fake_user': bool : if have fake user : default True
                                        }
                                case 2 : Real header
                }
            add_value_in_header : dict : default None
                {
                    name_of_key_in_header : function take just proxies in arg
                }
            '''
     
        if async_log:
            async_log_list.append(['INFO','Start to get_resp_request_async'])
        else:
            self.logger.info('Start to get_resp_request_async')
        try:
            exclud_str_in_html.append('csrf_token')
            for count in range(1, 6):
                await asyncio.sleep(random.randint(1, 30))
                try:
                    if async_log:
                        async_log_list.append(['INFO',f' -> Try to connect n°{count} :'])
                    else:
                        self.logger.info(f' -> Try to connect n°{count} :')
                        
                    proxies = None
                    if count < 5:
                        proxies = self.residential_proxies
                    elif count == 5 and semi_dedicated_proxies_list:
                        self.logger.warning('already 4 attempts with residential proxy -> try with semi dedicated proxies')
                        proxies = self.proxies_manager.get_random_proxy_from_a_list(proxies_list=semi_dedicated_proxies_list)

                    if proxies:
                        if async_log:
                            async_log_list.append(['INFO',f'    -> proxies : {proxies}'])
                        else:
                            self.logger.info(f'    -> proxies : {proxies}')                    
                
                        headers =None
                        if 'fake_header' in header.keys() and header['fake_header']:
                            headers = self.get_random_header(host=header['header']['host'],Referer= header['header']['referer'],Fake_user=header['header']['fake_user'],dict_key_value=dict_key_value)
                        elif 'fake_header' in header.keys() and not header['fake_header']:
                            headers = header['header']
                        else:
                            if async_log:
                                async_log_list.append(['WARNING','miss argument fake_header in param of fonction'])
                                return None, async_log_list
                            else:
                                self.logger.warning('miss argument fake_header in param of fonction')
                                return None
                
                        if add_value_in_header:
                            for key ,value in add_value_in_header.items():
                                headers[key] =value(proxies)
                        if async_log:
                            async_log_list.append(['INFO',f'    -> headers : {headers}'])
                            async_log_list.append(['INFO',f'    -> url : {url}'])
                        else:
                            self.logger.info(f'    -> headers : {headers}')
                            self.logger.info(f'    -> url : {url}')
                                
                        try:
                            response = None                  
                            if methode == 'GET':
                                async with session.get(url, 
                                                        headers=headers, 
                                                        proxy=proxies['http'],
                                                        timeout=timeout,
                                                        ssl=ssl,
                                                        params=params) as response:
                                    try:
                                        if response.status == 200 and not True in [str_check in await response.text() for str_check in exclud_str_in_html]:
                                            if async_log:
                                                async_log_list.append(['INFO','    -> Succes to connect'])
                                                return await response.text(),async_log_list
                                            else:
                                                self.logger.info('    -> Succes to connect')
                                                return await response.text()
                                        else:
                                            if async_log:
                                                async_log_list.append(['WARNING',f'    -> Echec to connect wong statue or wrong html, status_code is : {response.status}'])
                                                if 'csrf_token' in await response.text():
                                    
                                                    async_log_list.append('INFO',f'proxies reaload when request retry with this proxi')
                                            else:
                                                self.logger.warning(f'    -> Echec to connect wong statue or wrong html, status_code is : {response.status}')
                                                if 'csrf_token' in await response.text():
                            
                                                        self.logger.info(f'proxies reaload when request retry with this proxi')
                                    except Exception as error:
                                        if async_log:
                                            async_log_list.append(['ERROR',f'in try request async : {error}'])
                                        else:
                                            self.logger.error(f'in try request async : {error}')
                    
                            elif methode =='POST':
                                async with session.post(url, 
                                                        headers=headers, 
                                                        proxy=proxies['http'],
                                                        timeout=timeout,
                                                        ssl=ssl,
                                                        params=params,
                                                        data=data,
                                                        json=json) as response:
                                    try:
                                        if response.status == 200 and not True in [str_check in await response.text() for str_check in exclud_str_in_html]:
                                            if async_log:
                                                async_log_list.append(['INFO','    -> Succes to connect'])
                                                return await response.text(),async_log_list
                                            else:
                                                self.logger.info('    -> Succes to connect')
                                                return await response.text()
                                        else:
                                            if async_log:
                                                async_log_list.append(['WARNING',f'    -> Echec to connect wong statue or wrong html, status_code is : {response.status}'])
                                            else:
                                                self.logger.warning(f'    -> Echec to connect wong statue or wrong html, status_code is : {response.status}')
                                    except Exception as error:
                                        if async_log:
                                            async_log_list.append(['ERROR',f'in try request async post: {error}'])
                                        else:
                                            self.logger.error(f'in try request async post: {error}')
                        
                        except Exception as error:                                
                            if async_log:
                                async_log_list.append(['ERROR',f'Type error is : {type(error)}'])
                                async_log_list.append(['ERROR',f'in try request async: {error}'])
                            else:
                                self.logger.error(f'Type error is : {type(error)}')
                                self.logger.error(f'in try request async: {error}')
                    
                    else:
                        if async_log:
                            async_log_list.append(['ERROR','No proxy found -> return None'])
                            return None, async_log_list
                        else:
                            self.logger.error('No proxy found -> return None')
                            return None

                except Exception as error:
                    if async_log:
                        async_log_list.append(['ERROR',f" -> in param for request in get_resp_request_async: {error}"])
                    else:
                        self.logger.error(f" -> in param for request in get_resp_request_async: {error}")
        except Exception as error:
            if async_log:
                async_log_list.append(['ERROR',f'in get_resp_request_async : {error}'])
                return None, async_log_list
            else:
                self.logger.error(f'in get_resp_request_async : {error}')
            
                return None
