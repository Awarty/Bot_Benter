from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
import json
import time
import unidecode

def generate_prev_games_data_files(config, starting_url, max_weeks_back = 1, FILE_NAME=""):
    # Create webdriver
    options = Options()
    options.headless = config['headless']
    driver = webdriver.Chrome(config['driver_path'], options=options)

    driver.get(starting_url)
    result = []
    while max_weeks_back > 0:

        # Open all windows on current page
        # Find div with class name 'calendar-container'
        calendar = driver.find_element_by_class_name('calendar-container')
        # Loop through all divs in calendar
        for div in calendar.find_elements_by_class_name('calendar-date-container'):
            # Loop through all divs with class name 'calendar-game'
            for game in div.find_elements_by_class_name('calendar-game'):
                # Check if attribute 'data-isreult' is true in div with class name 'match-info'
                game_info = game.find_element_by_class_name('match-info')
                if game_info.get_attribute('data-isresult') == 'true':
                    # Open a new tab with the url of the game
                    driver.execute_script(f"window.open('{game_info.get_attribute('href')}');")

        # Go through all windows except the first one in reverse order ang get the data
        for handle in reversed(driver.window_handles[1:]):
            driver.switch_to.window(handle)
            result.append(get_game_data(driver, handle))
            # Print page title
            print(f'{driver.title}', flush=True)
            driver.close()

        # Switch back to the first window
        driver.switch_to.window(driver.window_handles[0])

        # Go to previous week if there is one
        # Check if button with xpath /html/body/div[1]/div[3]/div[2]/div/div/button[1] exists, if it does exit else click it
        button = driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div/div/button[1]')
        if button.get_attribute(name='disabled'):
            break

        button.click()
        max_weeks_back -= 1

    # Close last window
    driver.close()


    # Convert result to dataframes and save them to csvs
    (games_df, players_df) = game_convert_result_to_dfs(result)

    games_df.to_csv(f'./generated_data/{FILE_NAME}_games.csv', index=False, encoding='utf-8', header=True, sep=';')
    players_df.to_csv(f'./generated_data/{FILE_NAME}_players.csv', index=False, encoding='utf-8', header=True, sep=';')


def get_game_data(driver, handle):
    # Click on button with xpath /html/body/div[1]/div[3]/div[2]/div[1]/div/div[1]/div/label[3]
    driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[1]/div/label[3]').click()

    game_stats = {
        'game_id': int(driver.current_url.split('/')[-1]),
        'home_team': driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[4]/div[1]/div[2]/div').text,
        'away_team': driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[4]/div[1]/div[3]/div').text,
        'fthg': driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[4]/div[3]/div[2]/div').text,
        'ftag': driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[4]/div[3]/div[3]/div').text,
        'hxg': driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[4]/div[4]/div[2]/div').text,
        'axg': driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[2]/div[1]/div/div[4]/div[4]/div[3]/div').text,
        'date': driver.find_element_by_xpath('/html/body/div[1]/div[3]/ul/li[3]').text,
        'home_players': get_players_data(driver, handle, 'home'),
        'away_players': get_players_data(driver, handle, 'away')
    }

    return game_stats



def get_players_data(driver, handle, team):              
    if team == 'away':
        # find and click button with xpath /html/body/div[1]/div[3]/div[4]/div/div[1]/div/label[2]
        driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[4]/div/div[1]/div/label[2]').click()

    players = []
     # Loop through all tr in tbody with xpath '/html/body/div[1]/div[3]/div[4]/div/div[2]/table/tbody[1]'
    for tr in driver.find_element_by_xpath('/html/body/div[1]/div[3]/div[4]/div/div[2]/table/tbody[1]').find_elements_by_tag_name('tr'):
        tds = tr.find_elements_by_tag_name('td')
        # Get the href attribute from the first web element in tds
        href = tr.find_element_by_tag_name('a').get_attribute('href')
        player = {
            'name': unidecode.unidecode(tds[1].text),
            'id': int(href.split('/')[-1]),
            'pos': tds[2].text,
            'min': int(tds[3].text),
            'sh': int(tds[4].text),
            'g': int(tds[5].text),
            'kp': int(tds[6].text),
            'a': int(tds[7].text),
            'xg': float(tds[8].text.split('+')[0].split('-')[0]),
            'xa': float(tds[9].text.split('+')[0].split('-')[0]),
        }
        players.append(player)

    return players


def game_convert_result_to_dfs(res_in):
    games_df = pd.DataFrame()
    players_df = pd.DataFrame()

    for game in res_in:
        new_game_row = pd.DataFrame([
            [
                game['game_id'],
                game['home_team'],
                game['away_team'],
                game['fthg'],
                game['ftag'],
                game['hxg'],
                game['axg'],
                game['date']
            ]
        ], columns=['game_id', 'home_team', 'away_team', 'fthg', 'ftag', 'hxg', 'axg', 'date'])
        games_df = pd.concat([games_df, new_game_row])

        for team_str in ["home", "away"]:
            opp = "home" if team_str == "away" else "away"
            for player in game[team_str + "_players"]:
                new_player_row = pd.DataFrame([
                    [
                        game['game_id'],
                        game[team_str + '_team'],
                        game[opp + '_team'],
                        player['name'],
                        player['id'],
                        player['pos'],
                        player['min'],
                        player['sh'],
                        player['g'],
                        player['kp'],
                        player['a'],
                        player['xg'],
                        player['xa']
                    ]  
                ],
                columns=['game_id', 'team', 'opp', 'name', 'id', 'pos', 'min', 'sh', 'g', 'kp', 'a', 'xg', 'xa'])
                players_df = pd.concat([players_df, new_player_row])
        
    return (games_df, players_df)


if __name__ == "__main__":
    SITES = [('https://understat.com/league/EPL/2021', "EPL_2021"),]
    
    # Read json from file ./../config.cfg
    with open('./../config.cfg') as json_file:
        config = json.load(json_file)

    for site, name in SITES:
        generate_prev_games_data_files(config, site, 25, name)