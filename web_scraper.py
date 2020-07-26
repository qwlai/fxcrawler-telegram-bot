from FSMScraper import FSMScraper

def main():
    scraper = FSMScraper('https://secure.fundsupermart.com/fsm/foreign-exchange-rates')
    fx_dict = scraper.get_fx_rate()
    scraper.store_fx_rate_in_db(fx_dict)
    scraper.tear_down()
    
if __name__ == '__main__':
    main()