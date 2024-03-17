#!/usr/bin/python3
# coding: utf8

import logging
from logging_loki import LokiHandler, emitter
from datetime import date

class Logger():
    
    def __init__(self, script_name, environment, version, source, departement, log_level=logging.INFO):
        '''
        Init logger.
        
        Args:
        script_name (str) : Name of script that use this package. Needed for store logs in Grafana. (required)
        environment (str) : Environment name ['dev'/'prod'] (required)
        version (str) : Script that use this package version number ex : "1" (required)
        log_level : Log level [logging.DEBUG / logging.INFO / logging.WARNING / logging.ERROR / logging.CRITICAL] [default=logging.INFO]
       
        - for terminal : logger(script_name, environment['dev'/'prod'], self.version[int_versionning], log_level=[default=logging.INFO]).get(logger_type="terminal")
        - for file output : logger(script_name, environment['dev'/'prod'], self.version[int_versionning], log_level=[default=logging.INFO]).get(logger_type="file", log_file[default=None])
        - for grafana : logger(script_name, environment['dev'/'prod'], self.version[int_versionning], log_level=[default=logging.INFO]).get(logger_type="grafana", loki_endpoint, loki_user, loki_password)
        '''
        self.script_name, self.environment, self.version, self.source, self.departement, self.log_level = script_name, environment, version, source, departement, log_level


    def get(self, loki_endpoint=None, loki_user=None, loki_password=None, logger_type='grafana', logfile=None):
        '''
        Get logger from logger_type [grafana, file, terminal].
        
        Args:
        loki_endpoint (str) : Loki endpoint to send logs on Gradana [default=None]
        loki_user (str) : Loki user [default=None]
        loki_password (str) : Loki password [default=None]
        logger_type (str) : ['grafana' / 'file' / 'terminal']
        logfile (str) : logfile path [default=None]
        
        Returns:
        logger
        '''
        self.loki_endpoint, self.loki_user, self.loki_password, self.logger_type, self.logfile = loki_endpoint, loki_user, loki_password, logger_type, logfile
        self.handler = self._grafana_handler() if self.logger_type=='grafana' else self._terminal_or_file_handler()
        logger = logging.getLogger(self.script_name)
        logger.setLevel(self.log_level)
        
        logger.addHandler(self.handler)
        
        logger.info(f"logger {self.script_name} (ver: {self.environment}.{self.version}) initialised")

        return logger


    def _grafana_handler(self):
        emitter.LokiEmitter.level_tag = "level"
        return LokiHandler(
                    url=self.loki_endpoint, 
                    tags={"script": self.script_name, 
                          "date": f'{str(date.today())}', 
                          "env":f"{self.environment}.{self.version}",
                          "source_scraps": self.source,
                          "departement_scraps": self.departement
                         },
                    auth=(self.loki_user, self.loki_password),
                    version="1", # is not app version, is for Loki :) 
                    )
        
        
    def _terminal_or_file_handler(self):
        _formating = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler = logging.FileHandler(self.logfile) if self.logger_type == 'file' else logging.StreamHandler()
        handler.setFormatter(_formating)
        return handler
