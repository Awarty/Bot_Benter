from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
import json
import time
import unidecode
import os
import fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def generate_lineups_data_files(config):
    # Create webdriver
    options = Options()
    options.headless = config['headless']
    driver = webdriver.Chrome(config['driver_path'], options=options)

    for site_name, site_urls in config['league_links'].items():
        # Read all_names from prev_games csv files
        try:
            prev_games = pd.read_csv(f'./../prev_games/generated_data/{site_name}_players.csv', sep=';')
        except FileNotFoundError:
            raise FileNotFoundError(f'{site_name}_players.csv file not found, run prev_games before')

        site_url = site_urls['lineup']
        driver.get(site_url)
        
        # find and click button with xpath '//*[@id="onetrust-accept-btn-handler"]'
        try:
            driver.find_element_by_xpath('//*[@id="onetrust-accept-btn-handler"]').click()
        except:
            pass
        
        result = []
        
        # Get all divs with class 'shirt-ico icon icon--standing'
        shirt_divs = driver.find_elements_by_class_name('shirt-ico')
        for shirt_div in shirt_divs:
            # Click on the shirt div
            shirt_div.click()

        # Loop trough all windows open except the first one
        for window in driver.window_handles[1:]:
            driver.switch_to.window(window)
            
            # Get team names from xpath '/html/body/div[2]/div/div[4]/div[2]/div[4]/div[2]/a'
            home_team_name = driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[2]/div[4]/div[2]/a').text
            away_team_name = driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[4]/div[4]/div[1]/a').text
            date_time = driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[1]/div').text

            # Get team divs from xpath '/html/body/div[2]/div/div[9]/div[1]/div[2]/div/div[1]'
            home_team_div = driver.find_element_by_xpath('/html/body/div[2]/div/div[8]/div[1]/div[2]/div/div[1]')
            away_team_div = driver.find_element_by_xpath('/html/body/div[2]/div/div[8]/div[1]/div[2]/div/div[2]')

            # Loop trough all divs with class 'lf__participant'
            for index, team_div in enumerate([home_team_div, away_team_div]):
                for team_div_childs in team_div.find_elements_by_class_name('lf__participant'):
                    # Get name of player from a tag text
                    player_name = team_div_childs.find_element_by_tag_name('a').text
                    team = 'home' if index == 0 else 'away'
                    team_name = home_team_name if team == 'home' else away_team_name
                    result.append({
                        'date': date_time.split(' ')[0].replace('.', '-'),
                        'time': date_time.split(' ')[1],
                        'team': team,
                        'team_name': team_name,
                        'player_name': player_name.split('(')[0],
                        'home_team_name': home_team_name,
                        'away_team_name': away_team_name
                    })
            
            driver.close()

        driver.switch_to.window(driver.window_handles[0])

        if not os.path.exists("./generated_data"):
            os.makedirs("./generated_data")

        if result:
            # Create and save dataframe from result
            df = pd.DataFrame(result)
            
            # Convert date to datetime
            df["date"] = pd.to_datetime(df["date"], format='%d-%m-%Y')
            
            # Convert names
            df = replace_names(df, prev_games, config['name_replace_threshold'])

            df.to_csv(f'./generated_data/{site_name}_lineups.csv', index=False, encoding='utf-8', header=True, sep=';')


    # Switch to newly opened window
    driver.close()


def replace_names(df, prev_games, threshold=0):
    #Casting the name column of both dataframes into lists
    df_names = list(df.player_name.unique())
    prev_games_names = list(prev_games.name.unique())    

    name_dict = {}
    for x in df_names:
        (new_name, score) = process.extractOne(x, prev_games_names)
        if score > threshold:
            name_dict[x] = new_name
        else:
            print(f"WARNING: Could not find name to replace with {x}")
            
    # Pretty print name_dict
    print(json.dumps(name_dict, indent=4))

    #Using the dictionary to replace the keys with the values in the 'name' column for the second dataframe
    df.player_name = df.player_name.replace(name_dict)
    print(df)
    
    return df

if __name__ == '__main__':
    # Read json from file ./../config.cfg
    with open('./../config.cfg') as json_file:
        config = json.load(json_file)
    
    generate_lineups_data_files(config)