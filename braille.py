from string import ascii_lowercase
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time 
import os

text_id = 'maintext'
download_button_id = 'savestl'

options = FirefoxOptions()
options.add_argument("--headless")
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.manager.showWhenStarting", False)
current_dir = os.path.dirname(os.path.realpath(__file__))
# merge path with folder
download_dir = os.path.join(current_dir, 'letters')
options.set_preference("browser.download.dir", download_dir)
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")

driver = webdriver.Firefox(options=options)
driver.get("https://touchsee.me")


for c in ascii_lowercase:
    # fill text with c
    driver.find_element_by_id(text_id).clear()
    driver.find_element_by_id(text_id).send_keys(c)

    time.sleep(1)

    # click download button
    element = driver.find_element_by_id(download_button_id)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(0.5)

driver.close()

os.chdir(download_dir)

for i, f in enumerate(sorted(os.listdir(), key=os.path.getctime)):
    os.rename(f, ascii_lowercase[i] + '.stl')
