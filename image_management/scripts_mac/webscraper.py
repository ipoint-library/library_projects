import os
import requests
import base64
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import platform

class Webscraper:
    def __init__(self):
        self.options=None
        self.service=None
        self.driver=None
        self.connect()

    def connect(self):
        # Set up the Firefox webdriver
        self.options = Options()
        self.options.add_argument('-headless')
        if platform.system() == "Darwin":
            firefox_binary_path = '/drivers/firefox-bin'  # Adjust the path based on your system
            # '/Applications/Firefox.app/Contents/MacOS/firefox-bin'
            binary = FirefoxBinary(firefox_binary_path)

        else:
            self.service = Service('\\drivers\\geckodriver.exe')

        self.driver = webdriver.Firefox(service=self.service, options=self.options)

    def search_and_click(self, query, directory):
        directory = directory
        # Go to Google Images
        self.driver.get('https://www.google.com/imghp')

        try:
            search_input = self.driver.find_element(By.NAME, 'q')
            search_input.send_keys(query)
            search_input.send_keys(Keys.RETURN)

            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div#islrg')))
        except Exception as e:
            pass

        try:
            image_link = self.driver.find_element(By.CSS_SELECTOR, 'div#islrg a')
            image_link.click()
            print(f"image element for {query} found. Downloading.")
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img.rg_i')))
        except NoSuchElementException:
            print(f"Image element for {query} not found. Continuing to the next item.")
            return
        except ElementNotInteractableException:
            print(f"Image link for {query} could not be scrolled into view. Continuing to the next item.")
            return
        except Exception as e:
            pass

        image = self.driver.find_element(By.CSS_SELECTOR, 'img.rg_i')
        image_url = image.get_attribute('src')

        file_extension = ".jpg" if "jpeg" in image_url else ".png"

        file_name = os.path.join(directory, query.split(" ")[-1].replace("/", "-") + file_extension)
        self.download_image(image_url, file_name)

    def download_image(self, image_url, save_path):
        if image_url.startswith('http'):
            response = requests.get(image_url)
            response.raise_for_status()

            with open(save_path, 'wb') as file1:
                file1.write(response.content)
        else:
            image_data = base64.b64decode(image_url.split(',')[1])
            try:
                with open(save_path, 'wb') as file1:
                    file1.write(image_data)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Error downloading image: {e}")

    def scrape_list(self, partNumbers, download_directory="~/Documents/ProductPhotos", disconnect=True):
        record_number = 1

        for brand, partNumber in partNumbers:
            item = brand + " " + partNumber
            file_name = os.path.join(download_directory, item.split(" ")[-1].replace("/", "-") + ".jpg")
            file_name2 = os.path.join(download_directory, item.split(" ")[-1].replace("/", "-") + ".png")

            if record_number % 5 == 0:
                print(f"Processing Record {record_number} of {len(partNumbers)}: {item}")

            if not (os.path.isfile(file_name) or os.path.isfile(file_name2)):
                self.search_and_click(item, download_directory)
            record_number += 1

        if disconnect:
            self.driver.quit()

    def scrape_file(self, list_directory="~/Documents/MissingPhotos.csv", download_directory="~/Documents/ProductPhotos", reverse=False, disconnect=True):
        directory = download_directory
        part_numbers_file = list_directory

        PartNumbersList = []
        with open(part_numbers_file, 'r') as file:
            reader = csv.reader(file)
            for line in reader:
                PartNumbersList.append(line[0] + " " + line[1])

        begin = 0
        end = len(PartNumbersList) - 1
        record_number = 0

        if reverse:
            for item in PartNumbersList[end:begin:-1]:
                record_number += 1
                file_name = os.path.join(directory, item.split(" ")[-1] + ".jpg")
                file_name2 = os.path.join(directory, item.split(" ")[-1] + ".png")

                if record_number % 5 == 0:
                    print(f"Processing Record {record_number} of {end-begin}: {item}")

                if not (os.path.isfile(file_name) or os.path.isfile(file_name2)):
                    self.search_and_click(item, directory)
        else:
            for item in PartNumbersList[begin:end]:
                record_number += 1
                file_name = os.path.join(directory, item.split(" ")[-1] + ".jpg")
                file_name2 = os.path.join(directory, item.split(" ")[-1] + ".png")

                if record_number % 5 == 0:
                    print(f"Processing Record {record_number} of {end-begin}: {item}")

                if not (os.path.isfile(file_name) or os.path.isfile(file_name2)):
                    self.search_and_click(item, directory)

        if disconnect:
            self.driver.quit()

    def quit(self):
        self.driver.quit()
