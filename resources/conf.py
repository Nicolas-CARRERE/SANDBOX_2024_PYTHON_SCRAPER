from dotenv import load_dotenv
import os

class Conf():
    def __init__(self):
        load_dotenv('.env')

        self.championship_list = {
            'basque_union': os.getenv('URL1'),
            'territorial_committee': os.getenv('URL2'),
        }