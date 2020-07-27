from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from datetime import datetime as dt
from TelegramUtils import TelegramUtils
from pymongo import MongoClient
import re


class FSMScraper():
    """
    Contains functions related to scraping the website and storing the fx rate in database.
    """

    def __init__(self, url):
        """
        Sets up a selenium web driver and database
        """
        self.URL = url
        self.driver = self.create_driver()
        self.delay = 5
        self.telegram = TelegramUtils()

        try:
            self.mongo_client = MongoClient(port=27017)
            self.db = self.mongo_client["FSMOne"]
            self.fx_rate_history_col = self.db['fx_rate_history']
            print("Connected to database successfully.")
        except:
            print("Could not connect to database.")

    def create_driver(self):
        """
        Returns:
        driver - a firefox webdriver
        """

        opts = Options()
        opts.headless = True

        driver = webdriver.Firefox(options=opts)
        driver.get(self.URL)

        return driver

    def get_fx_rate(self):
        """
        Returns:
        fx_dict - containing details about the date of retrieval and the fx rates
        """
        try:
            sgd_to_usd = WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="content"]//*/table/tbody[2]/tr[9]/td[3]')))
            usd_to_sgd = WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="content"]//*/table/tbody[1]/tr[9]/td[2]')))

        except TimeoutException:
            print("Loading took too much time!")

        fx_dict = {
            "Date": dt.now(),
            "SGD_to_USD": sgd_to_usd.text,
            "USD_to_SGD": usd_to_sgd.text
        }

        return fx_dict

    def store_fx_rate_in_db(self, fx_dict):
        """
        Stores the fx rate into db and sends a message to telegram stating new fx rate
        """
        try:
            self.fx_rate_history_col.insert_one(fx_dict)
            print("One record inserted successfully at %s." % fx_dict['Date'])
            message_details = self.prepare_message_for_telegram(fx_dict)
            
            if (message_details['is_old_sgd_to_usd_better'] or message_details['is_old_usd_to_sgd_better']) and message_details['is_rate_updated']:
                self.telegram.send_message(message_details['bot_message'])
            else:
                if message_details['is_new_record']:
                    self.telegram.send_message(message_details['bot_message'])
                else:
                    return  
                
        except Exception as e:
            print("An Exception %e has occurred.", e)

    def prepare_message_for_telegram(self, fx_dict):
        """
        Prepares a message to telegram to update about fx rate
        """

        date_message = "__*%s*__" % fx_dict['Date'].strftime(
            "%d/%b/%Y %H:%M:%S")
        sgd_to_usd_message = "SGD\-USD rate: *%s*" % re.escape(
            fx_dict['SGD_to_USD'])
        usd_to_sgd_message = "USD\-SGD rate: *%s*" % re.escape(
            fx_dict['USD_to_SGD'])

        is_old_sgd_to_usd_better = False
        is_old_usd_to_sgd_better = False

        best_sgd_to_usd, best_usd_to_sgd, size = self.get_historical_best_rate()
        
        best_sgd_to_usd_message = "SGD\-USD: *%s* on *%s*" % (re.escape(
            best_sgd_to_usd['SGD_to_USD']), best_sgd_to_usd['Date'].strftime("%d/%b/%Y %H:%M:%S"))
        best_usd_to_sgd_message = "USD\-SGD: *%s* on *%s*" % (re.escape(
            best_usd_to_sgd['USD_to_SGD']), best_usd_to_sgd['Date'].strftime("%d/%b/%Y %H:%M:%S"))

        if best_sgd_to_usd is not None:
            if float(best_sgd_to_usd['SGD_to_USD']) > float(fx_dict['SGD_to_USD']):
                is_old_sgd_to_usd_better = True

        if best_usd_to_sgd is not None:
            if float(best_usd_to_sgd['USD_to_SGD']) > float(fx_dict['USD_to_SGD']):
                is_old_usd_to_sgd_better = True

        best_rate_message = "__*Historical Best Rates*__"

        if is_old_sgd_to_usd_better and is_old_usd_to_sgd_better:
            bot_message = "%s\n%s\n%s\n\n%s\n%s\n%s" % (
                date_message, sgd_to_usd_message, usd_to_sgd_message, best_rate_message, best_sgd_to_usd_message, best_usd_to_sgd_message)
        elif is_old_usd_to_sgd_better:
            bot_message = "%s\n%s\n%s\n\n%s\n%s" % (
                date_message, sgd_to_usd_message, usd_to_sgd_message, best_rate_message, best_usd_to_sgd_message)
        elif is_old_sgd_to_usd_better:
            bot_message = "%s\n%s\n%s\n\n%s\n%s" % (
                date_message, sgd_to_usd_message, usd_to_sgd_message, best_rate_message, best_sgd_to_usd_message)
        else:
            bot_message = "%s\n%s\n%s" % (
                date_message, sgd_to_usd_message, usd_to_sgd_message)
            
        return {
            'is_old_sgd_to_usd_better' : is_old_sgd_to_usd_better,
            'is_old_usd_to_sgd_better' : is_old_usd_to_sgd_better,
            'is_new_record' : True if size == 1 else False,
            'is_rate_updated': self.is_rate_updated(fx_dict), 
            'bot_message' : bot_message
        }

    def get_historical_best_rate(self):
        """
        Returns the historical best fx rate
        """
        size = self.fx_rate_history_col.find().sort(
            [("SGD_to_USD", -1), ("Date", -1)]).limit(2)
        best_sgd_to_usd = self.fx_rate_history_col.find().sort(
            [("SGD_to_USD", -1), ("Date", -1)]).limit(1)[0]
        best_usd_to_sgd = self.fx_rate_history_col.find().sort(
            [("USD_to_SGD", -1), ("Date", -1)]).limit(1)[0]
        return best_sgd_to_usd, best_usd_to_sgd, size.count()
    
    def is_rate_updated(self, fx_dict):
        """
        Returns True is rate is updated, otherwise False
        """
        previous_record = self.fx_rate_history_col.find().sort(
            [("Date", -1)]).limit(2)[1]
    
        if previous_record['SGD_to_USD'] == fx_dict['SGD_to_USD'] and previous_record['USD_to_SGD'] == fx_dict['USD_to_SGD']:
            return False
        return True
        

    def tear_down(self):
        """
        Tears down the web driver
        """
        self.driver.close()
