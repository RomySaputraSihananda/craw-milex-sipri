import os
import scrapy
import logging
import pytz

from datetime import datetime
from logging import handlers
from time import perf_counter
from time import time
from json import dumps

from scrapy.crawler import CrawlerProcess
from scrapy.http.response.html import HtmlResponse

from selenium import webdriver;
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

logging.basicConfig(level=logging.INFO, format='%(asctime)s [ %(levelname)s ] :: %(message)s', datefmt="%Y-%m-%dT%H:%M:%S", handlers=[
    handlers.RotatingFileHandler('debug.log'),  
    logging.StreamHandler()  
])

options: Options = Options()
options.add_argument('--headless')
options.add_argument("--kiosk-printing")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-notifications")
options.add_argument("--disable-web-security")
options.add_argument("--allow-running-insecure-content")
options.add_argument("--disable-save-password-bubble")
options.add_argument("--disable-extensions")
options.add_experimental_option("prefs", {
    "savefile.default_directory": f'{os.getcwd()}/data/xlsx',
    "download.default_directory": f'{os.getcwd()}/data/xlsx',
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    'profile.default_content_setting_values.automatic_downloads': 1
})


class Milex:
    def __init__(self) -> None:
        self.__url: str = 'https://milex.sipri.org/sipri' 
        self.__driver: WebDriver = webdriver.Chrome(options=options)
        self.__driver.set_window_size(1920, 1080)
    
    @staticmethod
    def counter_time(func):
        def counter(self):
            start: float = perf_counter()
            logging.info('start crawling')
            func(self)
            logging.info(f'task completed in {perf_counter() - start} seconds')
        
        return counter

    def __date_now(self) -> str:
        tz = pytz.timezone("Asia/Jakarta")
        date = datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")
        return date
    
    def __wait_element(self, selector: str, timeout: int = 300) -> WebElement:
        return WebDriverWait(self.__driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def __wait_download(self):
        if(not os.path.exists('data/xlsx')):
                os.makedirs('data/xlsx')

        try:
            WebDriverWait(self.__driver, 300).until(
                lambda x: 'SIPRI-Milex-data-1949-2023.xlsx' in os.listdir('data/xlsx')
            )
            logging.info("Download completed.")
        except TimeoutException:
            logging.error("Timed out waiting for download to complete.")
    
    @counter_time
    def start(self):
        self.__driver.get(self.__url)
        self.__driver.execute_script("window.scrollBy(0, 1000)");

        type_file: Select =  Select(self.__wait_element('.form-control.ng-untouched.ng-pristine.ng-valid'));
        type_file.select_by_index(1);

        description: str = self.__wait_element('#wide-div div:nth-child(2) p').text

        # for i in range(1, 2 + 1):
        for i in range(1, 174 + 1):
            country: WebElement = self.__wait_element(f'#countrySel1 option:nth-child({i})')
            country.click()

            country_name: str = country.text.strip(" ")
            file_name: str = country_name.lower().replace(" ", "_")

            self.__wait_element('.col-sm-4 .btn.btn-default.btn-block:nth-child(2)').click()

            self.__wait_element('.btn.btn-primary.btn-block').click()

            self.__wait_download()

            os.rename('data/xlsx/SIPRI-Milex-data-1949-2023.xlsx', f'data/xlsx/{file_name}.xlsx')

            with open(f'data/{file_name}.json', 'w') as file:
                file.write(dumps({
                    "link": self.__url, 
                    "domain": self.__url.split('/')[-2], 
                    "tag": self.__url.split('/')[2:],
                    "category": "SIPRI Military Expenditure Database", 
                    "description_category": description, 
                    "sub_category": "Country", 
                    "country_name": country_name, 
                    "file_name": f'{file_name}.xlsx',  
                    "path_data_raw": f'data/xlsx/{file_name}.xlsx', 
                    "crawling_at": self.__date_now(),
                    "crawling_time_epoch": int(time()),
                }, indent=2))
            
            logging.info(f'success extract country {country_name}')

            self.__wait_element('.col-sm-4 .btn.btn-default.btn-block:nth-child(5)').click()

        self.__driver.close()

if(__name__ == '__main__'):
    milex: Milex = Milex()
    milex.start()
