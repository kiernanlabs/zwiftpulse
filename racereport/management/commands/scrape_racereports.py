from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from racereport.models import Race, RaceCat, RaceResult, Team, ScrapeReport
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.chrome.options import Options as ChromeOptions

from selenium.webdriver import Chrome

import logging
import time
from time import sleep
import re
import os.path
import pytz

from django.conf import settings

logger = logging.getLogger('main')

# Note this script was originally as a standalone repo and used different variable / function naming conventions
# Too painful to fix right now

class Command(BaseCommand):
    help = 'scrapes and imports race results from zwiftpower into the database'

    def add_arguments(self, parser):
        parser.add_argument('count', nargs='?', default=20, type=int, help='number of URLs to scrape')
        parser.add_argument('--url', nargs='?', help="single URL to scrape")


    def initialize_driver_settings(self):
        opts = ChromeOptions()
        opts.headless = True
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--remote-debugging-port=9222")

        service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        # driver = webdriver.Chrome(service=service, options=opts)
        return {'options': opts, 'service': service}

    def handle(self, *args, **options):
        scrape_report = ScrapeReport(scrape_start=timezone.now(), completed=False)
        scrape_report.save()
        startTime = time.time()
        
        settings = self.initialize_driver_settings()
        with webdriver.Chrome(
            service=settings['service'], options=settings['options']
        ) as driver:
            if options['url'] != None: 
                logger.info(f"URL param found scraping {options['url']}")
                urls=[options['url']]
                options['count'] = 1

            else:
                # STEP 1: Get URLs to scrape
                urls = self.getRaceURLs("https://zwiftpower.com/", driver)
                logger.info(f"{len(urls)} New events found; up to scraping first {options['count']}")
                options['count'] = min(options['count'], len(urls))
                urls = urls[0:options['count']]
            
            successFinishes = 0
            finishErrorURLs = []
            successPrimes = 0
            primeErrorURLs = []

            for n, url in enumerate(urls) :
                logger.info(f"URL #{n+1}/{options['count']}: {url}")
                urlArray = [url]
                
                # STEP 2: For each URL, scrape the data
                # Currently doing one URL at a time and then saving; could do more
                results = self.scrape(urlArray, driver)  

                # STEP 3: For each race, save the data
                for (name, event) in enumerate(results.items()):
                    if event[1][0] is None: finishErrorURLs.append(url)
                    else: 
                        if self.save_finishes(event[0], event[1][0]):
                            successFinishes += 1
                        
                    if event[1][1] is None: primeErrorURLs.append(url)
                    else: 
                        successPrimes += 1
                        # Not currently storing prime data
                        # zwift_scrape.mkdirAndSave("primes", event[1][1], event[0])

            logger.info(f"==== [Run Report:{datetime.now(pytz.timezone('US/Eastern'))}] Total Execution time: {round((time.time() - startTime)/60,1)} minutes")
            logger.info(f"==== [Run Report:{datetime.now(pytz.timezone('US/Eastern'))}] Successful finish data scrapes: {successFinishes}/{options['count']}")
            logger.info(f"==== [Run Report:{datetime.now(pytz.timezone('US/Eastern'))}] Successful prime data scrapes: {successPrimes}/{options['count']}")
            logger.info(f"==== [Run Report:{datetime.now(pytz.timezone('US/Eastern'))}] events with scrape errors:")
            for errorUrl in finishErrorURLs:
                logger.info(f'==== [Run Report] * {errorUrl}')
            
            scrape_report.completed = True
            scrape_report.scrape_end = timezone.now()
            scrape_report.count_successful = successFinishes
            scrape_report.save()
            logger.info(f"==== [Scrape Report Object:{scrape_report}")

    '''===CORE SCRAPING FUNCTIONS==='''    
    '''Returns list of URLS to scrape'''    
    def getRaceURLs(self, urlpage, driver):
        
        logger.info("Scraping data from: {}.".format(urlpage))
        driver.get(urlpage)
        
        if len(driver.find_elements(By.XPATH, '//*[@id="login"]/fieldset/div/div[1]/div/a')) > 0: self.login(driver)
        
        logger.debug("collecting race URLs...")
        
        resultsButton = driver.find_element(By.XPATH, '//button[@id="button_event_results"]')
        resultsButton.click()
        filterButton = driver.find_element(By.XPATH, '//button[@id="button_event_filter"]')
        filterButton.click()
        raceButton = driver.find_element(By.XPATH, '//button[@data-value="TYPE_RACE"]')
        raceButton.click()
        sleep(3)
        results = driver.find_element(By.XPATH, '//*[@id="zwift_event_list"]/tbody')
        links = results.find_elements(By.TAG_NAME, "a")
        logger.debug(f"found {len(links)} events")

        urls = []
        for link in links:
            # only pull new races - unclear if needed
            event_id = self.toEventID(link.get_attribute("href"))
            # logger.debug(f'--Getting event_id for: {link.get_attribute("href")}')
            if event_id == "": break 
            
            race_objs = Race.objects.filter(event_id=event_id)
            if len(race_objs) == 0:
                urls.append(link.get_attribute("href"))
            elif race_objs[0].event_name == "unknown":
                urls.append(link.get_attribute("href"))
                logger.info(f"---adding {race_objs[0]} to list of urls due to unknown event_name")
            else:
                race_cats = RaceCat.objects.filter(race=race_objs[0])
                if len(race_cats) > 0 and race_cats[0].race_quality == 999 and race_objs[0].hours_ago < 4:
                    logger.info(f"---adding {race_objs[0]} to list of urls due to missing race_quality")
                    urls.append(link.get_attribute("href"))
        
        return urls
    
    
    '''scrapes data from specified URL'''    
    def scrape(self, urlpage, driver):
        scraped_data = {} 
        
        for n, url in enumerate(urlpage):
            logger.debug("--Scraping data from: {}.".format(url))
            finishData = []
            driver.get(url)

            logger.debug(f'--Getting new URL, current windows open: {len(driver.window_handles)}')
            
            try:
                if len(driver.find_elements(By.XPATH, '//*[@id="login"]/fieldset/div/div[1]/div/a')) > 0: self.login(driver)
                
                raceName = driver.find_element(By.XPATH, '//*[@id="header_details"]/div[1]/h3').text
                raceName = re.sub(r"[^A-Za-z0-9 ]+", "", raceName)
                raceName = self.toEventID(url) + " " + raceName
                
                # expecting <span data-value="1661013900" id="EVENT_DATE">Today 12:45</span>
                raceTimestamp = driver.find_element(
                        By.XPATH, '//*[@id="EVENT_DATE"]'
                    ).get_attribute('data-value')
                logger.info(f"--{n}:{raceName} - Downloading data")
            except:
                logger.debug(f'-- ERROR finding basic details on page, skipping scrape')
                continue #do next URL

            #Attempt to load the page
            try:
                _pages_loaded = WebDriverWait(driver, 1).until(
                    lambda driver: len(
                        driver.find_elements(
                            By.XPATH, '//*[@id="table_event_results_final_paginate"]/ul/li'
                        )[1:-1]
                    )
                    > 0
                )
            except:
                logger.info(f"--{n}:{raceName} - failed to load")
                continue #do next URL
            
            #Attempt to capture finish positions
            try:
                pages = driver.find_elements(
                    By.XPATH, '//*[@id="table_event_results_final_paginate"]/ul/li'
                )[1:-1]
                nPages = len(pages)
                columnButton = driver.find_element(By.XPATH, '//*[@id="columnFilter"]/button')
                columnButton.click()
                rankBeforeButton = driver.find_element(By.XPATH, '//*[@id="columnFilter"]//*[@id="table_event_results_final_view_27"]/span')
                rankEventButton = driver.find_element(By.XPATH, '//*[@id="columnFilter"]//*[@id="table_event_results_final_view_28"]/span')
                rankBeforeButton.location_once_scrolled_into_view
                rankBeforeButton.click()
                rankEventButton.click()
                results = driver.find_element(
                    By.XPATH, '//*[@id="table_event_results_final"]/tbody'
                )
                logger.debug("--Collecting finish data for all riders...")
                for n in range(2, nPages + 2):
                    if n > 2:
                        button = driver.find_element(
                            By.XPATH,
                            '//*[@id="table_event_results_final_paginate"]/ul/li[{}]/a'.format(
                                n
                            ),
                        )
                        name1 = (
                            results.find_elements(By.TAG_NAME, "tr")[0]
                            .find_elements(By.TAG_NAME, "td")[2]
                            .text
                        )
                        driver.execute_script("arguments[0].click();", button)
                        while (
                            results.find_elements(By.TAG_NAME, "tr")[0]
                            .find_elements(By.TAG_NAME, "td")[2]
                            .text
                            == name1
                        ):
                            results = driver.find_element(
                                By.XPATH, '//*[@id="table_event_results_final"]/tbody'
                            )
                    rows = results.find_elements(By.TAG_NAME, "tr")
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        category = cols[0].text
                        eventID = self.toEventID(url)
                        name = self.toName(cols[2].text)
                        team = self.toTeam(cols[2].text)
                        time = self.finishTime(cols[3].text)
                        rankBefore = cols[17].text
                        rankEvent = cols[18].text

                        # if there is a primes column, go one more
                        primeCol = results.find_elements(
                            By.XPATH, '//*[@id="table_event_results_final"]//th[@title="Points allocated for crossing the banner inside the top 10 on various laps."]'
                        )
                        if primeCol:
                            rankBefore = cols[18].text
                            rankEvent = cols[19].text
                        
                        finishData += [{"EventID": eventID, "EventTimestamp": raceTimestamp, "Name": name, "Team": team, "Category": category, "Time": time, "RankBefore": rankBefore, "RankEvent": rankEvent}]
                logger.info("--Found {} riders.".format(len(finishData)))
            except Exception as e:
                logger.info(f"--Failed to load finish data:{e}")
                finishData = []
            
            #Attempt to capture primes positions
            try:
                toPrimes = driver.find_element(By.XPATH, '//*[@id="zp_submenu"]/ul/li[4]/a')
                toPrimes.click()
                cButtons = driver.find_elements(
                    By.XPATH, '//*[@id="table_scroll_overview"]/div[1]/div[1]/button'
                )
                categoryBottons = [
                    but for but in cButtons if not (but.text == "" or but.text == "All")
                ]
                pButtons = driver.find_elements(
                    By.XPATH, '//*[@id="table_scroll_overview"]/div[1]/div[2]/button'
                )
                primeButtons = [but for but in pButtons if not but.text == ""]
                primeResults = driver.find_element(
                    By.XPATH, '//*[@id="table_event_primes"]/tbody'
                )
                n = 0
                while True:
                    try:
                        n = n + 1
                        testCell = (
                            primeResults.find_elements(By.TAG_NAME, "tr")[0]
                            .find_elements(By.TAG_NAME, "td")[3]
                            .text
                        )
                    except IndexError:
                        if n > 10 :
                            raise Exception("Timeout waiting for prime data")
                        sleep(0.25)
                    else:
                        break
                presults = {}
                primeButtons.reverse()
                for catBut in categoryBottons:
                    category = catBut.text
                    logger.debug("--Collecting prime data for category {}...".format(category))
                    presults[category] = {}
                    catBut.click()
                    for primeBut in primeButtons:
                        prime = primeBut.text
                        presults[category][prime] = {}
                        primeBut.click()
                        testCell2 = testCell
                        while testCell == testCell2:
                            try:
                                testCell2 = (
                                    driver.find_element(
                                        By.XPATH, '//*[@id="table_event_primes"]/tbody'
                                    )
                                    .find_elements(By.TAG_NAME, "tr")[0]
                                    .find_elements(By.TAG_NAME, "td")[3]
                                    .text
                                )
                            except StaleElementReferenceException:
                                testCell2 = testCell
                            sleep(0.25)

                        testCell = testCell2
                        primeResults = driver.find_element(
                            By.XPATH, '//*[@id="table_event_primes"]/tbody'
                        )
                        rows = primeResults.find_elements(By.TAG_NAME, "tr")
                        for row in rows:
                            cols = row.find_elements(By.TAG_NAME, "td")
                            lap = cols[0].text
                            splitName = cols[1].text
                            scores = {
                                self.toName(cols[n].text): self.primeTime(cols[n + 1].text, prime)
                                for n in range(2, len(cols), 2)
                                if not cols[n].text == ""
                            }
                            combinedName = "{}_{}".format(lap, splitName)
                            presults[category][prime][combinedName] = scores
            except Exception as e:
                logger.info(f"--Failed to load prime data")
                presults = []
            scraped_data[raceName] = [finishData, presults]
            logger.debug("--Formatting scraped data...")
        logger.debug("--Done.")
        return scraped_data

    '''Imports the scraped data into the database / models'''
    def save_finishes(self, event_name, rider_data):
        event_name_trim = event_name[8:]
        logger.info(f'--Attempting to save: {event_name_trim}')
        
        if rider_data == []:
            logger.info(f'--Error saving {event_name}, no rider data')
            return False

        event_datetime = datetime.fromtimestamp(int(rider_data[0]['EventTimestamp']), pytz.timezone("US/Eastern"))
        race_tuple = Race.objects.get_or_create(
                event_id=rider_data[0]['EventID'],
                defaults={'event_datetime': event_datetime, 'event_name': event_name_trim}
        )

        race = race_tuple[0]
        
        # update race with default data if found (sometimes races can be created with bad data)
        if race_tuple[1]==False:
            race.event_datetime = event_datetime
            race.event_name = event_name_trim
            race.save()
            
        # assume data is coming in sorted
        # need to count finishers by category
        finishers_by_category = {}

        for race_result in rider_data:
            finishers_by_category[race_result['Category']] = finishers_by_category.get(race_result['Category'],0)+1
            self.import_race_result(race, race_result, finishers_by_category[race_result['Category']])
        
        logger.info(f'--Saved {len(rider_data)} results')
        return True

    def import_race_result(self, race, row, position):
        race_cat_row = RaceCat.objects.get_or_create(
            race=race,
            category=row['Category']
        )[0]

        zp_rank_before = row['RankBefore']
        zp_rank_event = row['RankEvent']
        if zp_rank_before == '': zp_rank_before=0
        if zp_rank_event == '': zp_rank_event=0
        
        team_name = row['Team']
        if row['Team'] == '': team_name='None'
        team_obj = Team.objects.get_or_create(name=team_name)

        
        race_result = RaceResult.objects.update_or_create(
            race_cat = race_cat_row,
            racer_name = row['Name'],
            defaults={'team':team_obj[0], 'position': position, 'time_ms': row['Time'], 'zp_rank_before': zp_rank_before, 'zp_rank_event': zp_rank_event}
        )[0]
        
        # logger.debug(f'Successfully created: {race_result} | position {race_result.position}')
        
    
    '''Logs into ZwiftPower if needed as part of scraping process'''
    def login(self, driver):
        email = settings.ZWIFT_EMAIL
        password = settings.ZWIFT_PWD
        logger.info(f'Login required...')
        try:
            login_button = driver.find_element(
                    By.XPATH, '//*[@id="login"]/fieldset/div/div[1]/div/a'
            )
            login_button.click()
            emailField = driver.find_element(By.XPATH, '//input[@id="username"]')
            passwordField = driver.find_element(By.XPATH, '//input[@id="password"]')
            loginButton2 = driver.find_element(By.XPATH, '//button[@id="submit-button"]')
            emailField.send_keys(email)
            passwordField.send_keys(password)
            loginButton2.click()
        except:
            return None
    
    

    '''===HELPER FUNCTIONS FOR SCRAPING==='''        

    def toEventID(self, url):
        #expected URL format: https://zwiftpower.com/events.php?zid=3072775
        eventID = ""
        if len(url.split("zid=")) > 1:
            eventID = url.split("zid=")[1]
        return eventID

    def toTeam(self, string):
        #returns the team name if it exists
        team = ""
        if len(string.split("\n")) > 1:
            team = string.split("\n")[1]
        return team

    def toName(self, string):
        # print(string)
        name = string.split("\n")[0]
        # name = re.sub(r'[^A-Za-z0-9 ]+', '', name)
        # name = name.split(' ')[0]+' '+name.split(' ')[1]
        return name

    def secsToMS(self, string):
        flt = float(string)
        return int(flt * 1000)


    def hrsToMS(self, string):
        ints = [int(t) for t in string.split(":")]
        ints.reverse()
        time = 0
        for n, t in enumerate(ints):
            time += 1000 * t * (60**n)
        return time


    def toTime(self, string):
        if len(string.split(".")) == 1:
            return self.hrsToMS(string)
        else:
            return self.secsToMS(string)


    def finishTime(self, string):
        timeStrs = string.split("\n")
        if len(timeStrs) == 1:
            return self.toTime(timeStrs[0])
        else:
            time = self.toTime(timeStrs[0])
            if (timeStrs[0].split(".") == 1) and (timeStrs.split(".") < 1):
                tString = timeStrs[1].split(".")[1]
                tString = tString.replace("s", "")
                tString = "0." + tString
                if float(tString) < 0.5:
                    time -= 1000 - self.secsToMS(tString)
                else:
                    time += self.secsToMS(tString)
            return time


    def primeTime(self, string, prime):
        if prime == "First over line":
            if string == "":
                return 0
            else:
                string = string.replace("+", "")
                string = string.replace("s", "")
                return self.toTime(string)
        else:
            return self.finishTime(string)


    def getFinishPositions(self, sortP):
        currCat = None
        pos = 1
        positions = []
        for cat in sortP["Category"]:
            if currCat != cat:
                currCat = cat
                pos = 1
            positions += [pos]
            pos += 1
        return positions


    def getPrimePositions(self, sortP):
        currDesc = None
        pos = 1
        positions = []
        for _, row in sortP.iterrows():
            desc = "{}_{}_{}".format(row["Category"], row["Split"], row["Prime"])
            if desc != currDesc:
                currDesc = desc
                pos = 1
            positions += [pos]
            pos += 1
        return positions