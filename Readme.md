## Installation

This project requires Python 3.6+.

You will also need the following Python packages:

- Selenium (`pip install selenium`)
- BeautifulSoup (`pip install beautifulsoup4`)
- psycopg2 (`pip install psycopg2`)
- python-dotenv (`pip install python-dotenv`)

This project also uses ChromeDriver for Selenium. Follow the instructions [here](https://sites.google.com/a/chromium.org/chromedriver/getting-started) to install ChromeDriver for your operating system.

You will need to create a `.env` file in the root of your project and fill it with your environment variables for the database connection. The `dotenv` package is used to load these variables.