#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Async_log():
    def __init__(self, logger):
        self.list_logs_ads = []
        self.async_logs = []
        self.logger = logger
    def fill_list_logs_ads(self,list_logs):
        self.list_logs_ads.append(list_logs)

    def send_async_log(self):
        try:
            self.affect_value_to_async_list()
            if self.async_logs:
                for lists in self.async_logs:
                    for logs in lists:
                        if logs[0] == 'INFO':
                            self.logger.info(logs[1])

                        elif logs[0] == 'ERROR':
                            self.logger.error(logs[1])
                        
                        elif logs[0] == 'WARNING':
                            self.logger.warning(logs[1])
                        
                        elif logs[0] == 'CRITICAL':
                            self.logger.critical(logs[1])
            self.async_logs = []
        except Exception as error:
            self.logger.error(f"in send_async_log : {error}")

    def affect_value_to_async_list(self):
        try:
            if self.list_logs_ads and self.async_logs == []:
                self.async_logs = self.list_logs_ads.copy()
                if len(self.list_logs_ads) == len(self.async_logs):
                    self.list_logs_ads = []
                else:
                    self.async_logs = []
                    self.affect_value_to_async_list()
        except Exception as error:
            self.logger.error(f'in affect_value_to_async_list : {error}')