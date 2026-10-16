"""Code from "9.7 Selenium, compared" that is shown in the book but not run on its own:
it needs your own data, a server or extra setup, or it is one step of an example
that the book builds up gradually. See the book for details."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get(f"{BASE}/js-store/")
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".product")))
cards = driver.find_elements(By.CSS_SELECTOR, ".name")
names = [card.text for card in cards]
driver.quit()
