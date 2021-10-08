from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
import json
import time
import unidecode

def generate_current_games_data_files(config, starting_url, max_weeks_back=1, FILE_NAME=""):
    # Create webdriver
    options = Options()
    options.headless = config['headless']
    driver = webdriver.Chrome(config['driver_path'], options=options)

    log_in(driver, config['op_login']['username'], config['op_login']['password'])

    driver.get(starting_url)
    result = []

    # Find and click the button with xpath '/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[5]/div/div/div/div/p/a'
    driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[6]/div[1]/div/div[1]/div[2]/div[1]/div[5]/div/div/div/div/p/a').click()

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
                'date': current_date,
                'time': td_elements[0].text,
                'odds': get_odds_from_site(driver, href_to_game)
            })
    
    # Pretty print result
    #print(json.dumps(result, indent=4, sort_keys=True), flush=True)

    # Save result to file
    for game in result:
        game['odds'].to_csv(\
            f'./generated_data/{FILE_NAME}_{game["home_team"]}-{game["away_team"]}_{game["date"]}_{game["time"].replace(":", "%")}.csv',\
                index=False, header=True, sep=';')
        print(game['odds'])





def get_odds_from_site(driver, url):
    # Open a new tab with url
    driver.execute_script(f"window.open('{url}');")
    driver.switch_to.window(driver.window_handles[1])

    # Get from id 'odds-data-table'
    odds_table = driver.find_element_by_id('odds-data-table')

    # Get all element by class 'table-main detail-odds sortable
    odds_table_main = odds_table.find_elements_by_class_name('detail-odds')[0]
    

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



def log_in(driver, username_input='', password_input=''):
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
    SITES = [('https://www.oddsportal.com/soccer/england/premier-league/', "PL_2021"),
             ('https://www.oddsportal.com/soccer/italy/serie-a/', "SA_2021")]
    
    # Read json from file ./../config.cfg
    with open('./../config.cfg') as json_file:
        config = json.load(json_file)

    
    for site, name in tqdm(SITES):
        generate_current_games_data_files(config, site, 25, name)