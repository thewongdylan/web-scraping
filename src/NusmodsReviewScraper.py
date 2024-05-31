# Imports
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
from datetime import datetime
import time

import logging
logging.getLogger().setLevel(logging.INFO)

chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Global variables
logger = logging.getLogger(__name__)
nusmods_base_url = "https://nusmods.com/courses/"
reviews = "#reviews"

# Set up Chrome Driver
def start_driver() -> webdriver.Chrome:
    logger.info("Starting Chrome Driver")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Extract course name 
def get_course_name(course_code: str, driver: webdriver.Chrome) -> str:
    logger.info(f"Getting course name for {course_code}")
    url = nusmods_base_url + course_code + reviews
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'h1')))
    course_name = driver.find_element(By.CSS_SELECTOR, "h1").text.split("\n")[1]
    return course_name 

# Access given NUSMods course page
def access_webpage(driver: webdriver.Chrome):
    logger.info("Accessing NUSMods course page")

    # Find the review iframe and switch to it
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe')))

    iframes = driver.find_elements(By.TAG_NAME, 'iframe')

    if len(iframes) >= 2:
        # Get the second iframe, rest are for ads
        second_iframe = iframes[1]
    else:
        print("Review Iframe was not found.")

    driver._switch_to.frame(second_iframe)
    time.sleep(1) # Wait for iframe to load
    
    return driver

def extract_reviews(driver: webdriver.Chrome) -> pd.DataFrame:
    logger.info("Extracting reviews")

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Create dataframe to store reviews
    reviews_df = pd.DataFrame(columns=['Date','Author','Content'])

    post_list = soup.find("ul", class_="post-list")
    for post in post_list:
        author = post.find("span", class_="author").text

        date_str = post.find("a", class_="time-ago").get('title')
        date = datetime.strptime(date_str, "%A, %B %d, %Y %I:%M %p")

        post_message = post.find("div", class_="post-message").text

        temp_df = pd.DataFrame([[date, author, post_message]], 
                            columns=['Date','Author','Content'])
        
        reviews_df = pd.concat([reviews_df, temp_df], ignore_index=True)

    return reviews_df

# Overall function to scrape and export reviews
def scrape_reviews(course_code: str) -> pd.DataFrame:
    logger.info("Scraping reviews")

    driver = start_driver()
    course_name = get_course_name(course_code, driver)
    driver = access_webpage(driver=driver)
    reviews_df = extract_reviews(driver=driver)
    reviews_df.insert(0, 'Course Name', course_name)
    reviews_df.insert(0, 'Course Code', course_code)
    reviews_df.to_csv(f"data/{course_code} Reviews {datetime.now().date()}.csv", index=False)
    driver.quit()

    logger.info("Scraping complete")
    return reviews_df


def main():
    course_code = input()
    reviews_df = scrape_reviews(course_code)
    print(reviews_df.head(5))

if __name__ == "__main__":
    main()