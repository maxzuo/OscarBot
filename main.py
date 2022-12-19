# chromedriver: C:\Users\maxzu\Development\Python Programming\bingO\venv
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tqdm import tqdm

with open('keys.txt', 'r') as f:
  username, password = [c.strip() for c in f.readlines()]

OSCAR_BASE_URL = 'https://sso.gatech.edu/cas/login?'
OSCAR_WORKSHEET_URL = 'https://oscar.gatech.edu/bprod/bwskfreg.P_AltPin'
FORMAT_URL = 'https://oscar.gatech.edu/bprod/bwckschd.p_disp_detail_sched?term_in={}&crn_in={}'
AVAILABILITY_SELECTOR = 'tr'


def check(crn:str) -> bool:
  date_string = datetime.strftime(datetime.now(), '%Y%m')

  resp = requests.get(FORMAT_URL.format(date_string, crn))

  soup = BeautifulSoup(resp.content.decode('utf-8'), features='html.parser')
  table_rows = soup.select(AVAILABILITY_SELECTOR)

  for row in table_rows:
    header = row.select_one('th')
    if header is not None and header.text == 'Seats':
      _, _, remaining = row.select('td')
      # print(f'class: {crn}\tremaining seats:', remaining.text)
      if int(remaining.text.strip()) > 0:
        return True
      else:
        return False

  return True


def login(driver, wait):
    driver.get(OSCAR_BASE_URL)
    try:
        wait.until(EC.element_to_be_clickable((By.ID, 'username'))).send_keys(username)
        wait.until(EC.element_to_be_clickable((By.ID, 'password'))).send_keys(password)
    except Exception as e:
        raise e

    driver.find_element(By.CSS_SELECTOR, '#login > section.btn-row.buttons > input.btn.btn-submit.button').click()

    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'duo_iframe')))
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#auth_methods > fieldset > div.row-label.push-label > button'))).click()

        driver.switch_to.parent_frame()
    except Exception as e:
        raise e

    login_wait = WebDriverWait(driver, 25)
    try:
        login_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="logout"]')))
    except Exception as e:
        raise e


def register(crn:str) -> bool:
  options = webdriver.ChromeOptions()
  options.add_experimental_option('excludeSwitches', ['ignore-certificate-errors'])

  driver = webdriver.Chrome('./chromedriver.exe', options=options)
  wait = WebDriverWait(driver, 25)

  try:
    login(driver, wait)
  except:
    driver.close()
    return False

  driver.get('https://oscar.gatech.edu/')
  time.sleep(.1)
  driver.get('https://sso.sis.gatech.edu/ssomanager/c/SSB')
  time.sleep(.1)
  driver.get('https://oscar.gatech.edu/bprod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu')
  time.sleep(.1)
  driver.get(OSCAR_WORKSHEET_URL)



  try:
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'body > div.pagebodydiv > form > input[type=submit]'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'crn_id1'))).send_keys(crn)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'body > div.pagebodydiv > form > input[type=submit]:nth-child(28)'))).click()
  except Exception as e:
    driver.close()
    return False
  time.sleep(2)

  if 'closed' in driver.page_source.lower():
    return False

  driver.close()
  return True


def main():
  target_crns = [['83707']]

  with tqdm() as pbar:
    while len(target_crns):
      pbar.update()
      for crn_group in target_crns:
        skip_next = False
        for crn in list(crn_group):
          if check(crn):
            print(f'ADDING: {crn}')
            # do action
            if register(crn):
              crn_group.remove(crn)
            else:
              # email error
              pass
          else:
            skip_next = True
        if skip_next:
          break

      time.sleep(0.5)


if __name__ == '__main__':
  main()