from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
import json
import time
import unidecode
import os
from datetime import date, timedelta

def generate_current_games_data_files(config):
    """
        Generates a dataframe of all current games.
    """

    # Create webdriver
    options = Options()
    options.headless = config['headless']
    driver = webdriver.Chrome(config['driver_path'], options=options)

    log_in(driver, config['op_login']['username'], config['op_login']['password'])


    for site_name, site_urls in config['league_links'].items():
        site_url = site_urls['current_games']

        result = []
        driver.get(site_url)

        # Find and click the button with xpath '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[5]/div/div/div/div/p/a'
        try:
            driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[5]/div/div/div/div/p/a').click()
        except:
            pass

        # Get element with xpath '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/table/tbody'
        tbody = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/table/tbody')

        current_date = ''
        # Loop trough all tr elements
        for tr_element in tqdm(tbody.find_elements_by_tag_name('tr')):
            # If tr element has class 'center nob-border'
            if tr_element.get_attribute('class') == 'center nob-border':
                # Get the date
                current_date = tr_element.find_element_by_tag_name('th').find_element_by_tag_name('span').text

            # If tr element has attribute 'xeid'
            if tr_element.get_attribute('xeid') is not None:
                # Gete all td elements in tr element
                td_elements = tr_element.find_elements_by_tag_name('td')
                # Get all a elements in td elements
                a_elements = td_elements[1].find_elements_by_tag_name('a')

                # Get the href
                if len(a_elements) == 1:
                    href_to_game = a_elements[0].get_attribute('href')
                else:
                    href_to_game = a_elements[1].get_attribute('href')

                home_team = td_elements[1].text.split(' - ')[0][1:] if td_elements[1].text.split(' - ')[0][0] == ' ' else td_elements[1].text.split(' - ')[0]
                away_team = td_elements[1].text.split(' - ')[1][1:] if td_elements[1].text.split(' - ')[1][0] == ' ' else td_elements[1].text.split(' - ')[1]

                result.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'date': change_to_real_date(current_date),
                    'time': td_elements[0].text,
                    'odds': get_odds_from_site(driver, href_to_game)
                })

        if not os.path.exists("./current_games/generated_data"):
            os.makedirs("./current_games/generated_data")

        # Save result to file
        for game in result:
            game['odds'].to_csv(\
                f'./current_games/generated_data/current_game_{site_name}_{game["home_team"]}-{game["away_team"]}_{game["date"]}_{game["time"].replace(":", "%")}.csv',\
                    index=False, header=True, sep=';')
    
    # Close last window
    driver.close()


def change_to_real_date(in_date):
    # Get todays date
    today = date.today()

    # Check if date contains 'Today', 'Tomorrow' or 'Yesterday'
    if 'Today' in in_date:
        return str(today)
    elif 'Tomorrow' in in_date:
        return str(today + timedelta(days=1))
    elif 'Yesterday' in in_date:
        return str(today - timedelta(days=1))
    return in_date


def get_odds_from_site(driver, url):
    """
        Gets the odds from the given url.
    """

    # Open a new tab with url
    driver.execute_script(f"window.open('{url}');")
    driver.switch_to.window(driver.window_handles[1])

    # Get from id 'odds-data-table'
    odds_table = driver.find_element_by_id('odds-data-table')

    # Get all element by class 'table-main detail-odds sortable
    for i in range(0, 100):
        try:
            odds_table_main = odds_table.find_elements_by_class_name('detail-odds')[0]
            break
        except:
            time.sleep(1)
            print('Retrying...', flush=True)
    

    # Get first tbody
    odds_table_body = odds_table_main.find_elements_by_tag_name('tbody')[0]
    odds = []
    
    # Get all trs in tbody
    trs = odds_table_body.find_elements_by_tag_name('tr')
    for tr in trs:
        # Check if tr contains any td
        if tr.find_elements_by_tag_name('td'):
            odds.append(dict(zip(['Site', 'Home', 'Draw', 'Away'], [td.text for td in tr.find_elements_by_tag_name('td')])))

    # Create empty df
    odds_cleaned = pd.DataFrame(columns=['Site', 'Home', 'Draw', 'Away'])
    for odd in odds[:-1]:
        site = odd['Site'].replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '')
        odds_cleaned = odds_cleaned.append({'Site': site,
                            'Home': float(odd['Home']),
                            'Draw':float(odd['Draw']),
                            'Away': float(odd['Away'])}, ignore_index=True)

    # close window
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return odds_cleaned

def generate_avr_old_odds_file(config):
    # Create webdriver
    options = Options()
    options.headless = config['headless']
    driver = webdriver.Chrome(config['driver_path'], options=options)

    log_in(driver, config['op_login']['username'], config['op_login']['password'])

    for site_name, site_urls in config['league_links'].items():
        # Result df
        results = pd.DataFrame(columns=['date', 'time', 'home_team', 'away_team', 'result', 'odds_1', 'odds_X', 'odds_2'])

        current_page_nr = 1
        while (True):
            site_url = site_urls['current_games']+f"results/#/page/{current_page_nr}/"
            driver.get(site_url)
            time.sleep(1)

            try:
                test = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[6]/table/tbody/tr/td/div/ul/li/div')
                break
            except:
                pass

            # Get element with xpath '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[6]/table/tbody'
            tbody = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[6]/table/tbody')

            # Loop trough all tr elements
            for tr_element in tqdm(tbody.find_elements_by_tag_name('tr')):
                if tr_element.get_attribute('class') == 'center nob-border':
                    current_date = tr_element.find_element_by_tag_name('th').find_element_by_tag_name('span').text
                elif tr_element.get_attribute('class') != 'table-dummyrow' and tr_element.get_attribute('class') != 'dark center':
                    # get game time from td with class 'table-time'
                    game_time = tr_element.find_element_by_class_name('table-time').text
                    # Get team names by td with class 'name'
                    (home_team_name, away_team_name) = tr_element.find_element_by_class_name('name').text.split(' - ')
                    # Get result from td with class 'table-score'
                    result = tr_element.find_element_by_class_name('table-score').text
                    # Get all td's with the class 'odds-nowrp'
                    odds = tr_element.find_elements_by_class_name('odds-nowrp')

                    odds_1 = odds[0].text
                    odds_X = odds[1].text
                    odds_2 = odds[2].text

                    results = results.append({'date': change_to_real_date(current_date),
                                            'time': game_time,
                                            'home_team': home_team_name,
                                            'away_team': away_team_name,
                                            'result': result,
                                            'odds_1': odds_1,
                                            'odds_X': odds_X,
                                            'odds_2': odds_2}, ignore_index=True)

            current_page_nr += 1

        # Save results to csv
        results.to_csv(f'./generated_data/{site_name}_only_old_games.csv', index=False, header=True, sep=';')

        



def log_in(driver, username_input='', password_input=''):
    """
        Logs in to the site.
    """
    
    driver.get('https://www.oddsportal.com/login')

    # Find and write username_input to '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[2]/div/form/div[1]/div[2]/input'
    username = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/form/div[1]/div[2]/input')
    username.send_keys(username_input)

    # Find and write password_input to '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/form/div[2]/div[2]/input'
    password = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/form/div[2]/div[2]/input')
    password.send_keys(password_input)

    # press login button with xpath '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/form/div[3]/button'
    driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/form/div[3]/button').click()



if __name__ == "__main__":
    # Read json from file ./../config.cfg
    with open('./../config.cfg') as json_file:
        config = json.load(json_file)

    #generate_current_games_data_files(config)
    generate_avr_old_odds_file(config)