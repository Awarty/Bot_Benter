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


def generate_lineups_data_files(config, old=True):
    # Create webdriver
    options = Options()
    options.headless = config['headless']
    driver = webdriver.Chrome(config['driver_path'], options=options)

    for site_name, site_urls in config['league_links'].items():
        # Read all_names from prev_games csv files
        try:
            prev_games_player_df = pd.read_csv(f'./prev_games/generated_data/{site_name}_players.csv', sep=';')
            prev_games_team_df = pd.read_csv(f'./prev_games/generated_data/{site_name}_games.csv', sep=';')
        except FileNotFoundError:
            raise FileNotFoundError(f'{site_name}_players.csv file not found, run prev_games before')

        all_site_urls = [site_urls['lineup']]
        if old is True:
            all_site_urls.append(str(site_urls['lineup'])+"resultat/")

        result = []
        for site_url in all_site_urls:
            
            print(f'{site_name} - {site_url}')
            driver.get(site_url)
            
            # find and click button with xpath '//*[@id="onetrust-accept-btn-handler"]'
            try:
                driver.find_element_by_xpath('//*[@id="onetrust-accept-btn-handler"]').click()
            except:
                pass


            # Get div with xpath '/html/body/div[6]/div[1]/div/div[1]/div[2]/div[4]/div[2]/div[1]/section[2]/div[2]'
            if site_url == all_site_urls[0]:
                print(driver.current_url)
                full_div = driver.find_element_by_xpath('/html/body/div[6]/div[1]/div/div[1]/div[2]/div[4]/div[2]/div[1]/section[2]/div[2]')
            else:
                # print current site url
                print(driver.current_url)
                full_div = driver.find_element_by_xpath('/html/body/div[6]/div[1]/div/div[1]/div[2]/div[4]/div[2]/div[1]/div[1]/div/div')


            # Get all divs with classes 'event__match--static'
            divs = full_div.find_elements_by_class_name('event__match--twoLine')
            print(f'{site_name + "-" + site_url}: {len(divs)} games found', flush=True)
            for div in tqdm(divs):
                if site_url == all_site_urls[0]:
                    # Check if div contains a svg with class 'shirt-ico'
                    try: 
                        if div.find_element_by_class_name('shirt-ico'):
                            # Click on div
                            driver.execute_script("arguments[0].click();", div)
                            result += get_results(driver)
                    except:
                        pass
                else:
                    # Click on div
                    driver.execute_script("arguments[0].click();", div)
                    result += get_results(driver)
                    

        if not os.path.exists("./generated_data"):
            os.makedirs("./generated_data")

        if result:
            # Create and save dataframe from result
            df = pd.DataFrame(result)
            
            # Convert date to datetime
            df["date"] = pd.to_datetime(df["date"], format='%d-%m-%Y')
            
            # Convert names
            df = replace_names(df, prev_games_player_df, prev_games_team_df, config['name_replace_threshold'])

            df.to_csv(f'./generated_data/{site_name}_lineups.csv', index=False, encoding='utf-8', header=True, sep=';')
            
    # Switch to newly opened window
    driver.switch_to.window(driver.window_handles[-1])
    driver.close()


def get_results(driver):
    result = []
    driver.switch_to.window(driver.window_handles[1:][-1])
    
    # goto '#matchsummering/uppstallning'
    new_url = driver.current_url.split('#')[0]+"#matchsummering/uppstallning"
    driver.get(new_url)

    # Wait until xpath '/html/body/div[2]/div/div[4]/div[2]/div[4]/div[2]/a' exists
    for i in range(0, 1000):
        try:
            driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[2]/div[4]/div[2]/a')
            break
        except:
            time.sleep(0.1)
            print(f'{i}', flush=True)
            print(driver.current_url, flush=True)
            pass

    # Get team names from xpath '/html/body/div[2]/div/div[4]/div[2]/div[4]/div[2]/a'
    home_team_name = driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[2]/div[4]/div[2]/a').text
    away_team_name = driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[4]/div[4]/div[1]/a').text
    date_time = driver.find_element_by_xpath('/html/body/div[2]/div/div[4]/div[1]/div').text

    for i in range(0, 1000):
        try:
            try:
                home_team_div = driver.find_element_by_xpath('/html/body/div[2]/div/div[8]/div[1]/div[2]/div/div[1]')
                away_team_div = driver.find_element_by_xpath('/html/body/div[2]/div/div[8]/div[1]/div[2]/div/div[2]')
                break
            except:
                try:
                    home_team_div = driver.find_element_by_xpath('/html/body/div[2]/div/div[9]/div[1]/div[2]/div/div[1]')
                    away_team_div = driver.find_element_by_xpath('/html/body/div[2]/div/div[9]/div[1]/div[2]/div/div[2]')
                    break
                except:
                    pass
        except:
            time.sleep(0.1)
            print(f'{i}', flush=True)
            print(driver.current_url, flush=True)


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

    return result




def find_best(df_names, prev_games_names, threshold):
    result = {}
    for x in df_names:
        (new_name, score) = process.extractOne(x, prev_games_names)
        if score > threshold:
            if x in result:
                print(f"Found more than one for {x}")
            result[x] = new_name
        else:
            print(f"WARNING: Could not find name to replace with {x}")
    return result

def replace_names(df, prev_games_player_df, prev_games_team_df, threshold=0):
    #Casting the name column of both dataframes into lists
    df_names = list(df.player_name.unique())
    df_team_names = list(df.team_name.unique()) +\
                    list(df.home_team_name.unique()) +\
                    list(df.away_team_name.unique())
    df_team_names = list(set(df_team_names))

    prev_games_names = list(prev_games_player_df.name.unique())
    prev_games_team_names = list(prev_games_team_df.home_team.unique()) +\
                            list(prev_games_team_df.away_team.unique())
    prev_games_team_names = list(set(prev_games_team_names))

    name_dict = find_best(df_names, prev_games_names, threshold)
    team_name_dict = find_best(df_team_names, prev_games_team_names, threshold)

    
    #Using the dictionary to replace the keys with the values in the 'name' column for the second dataframe
    df.player_name = df.player_name.replace(name_dict)
    df.team_name = df.team_name.replace(team_name_dict)
    df.home_team_name = df.home_team_name.replace(team_name_dict)
    df.away_team_name = df.away_team_name.replace(team_name_dict)
    
    return df

if __name__ == '__main__':
    # Read json from file ./../config.cfg
    with open('./../config.cfg') as json_file:
        config = json.load(json_file)
    
    generate_lineups_data_files(config)