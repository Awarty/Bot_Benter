	
import pandas as pd
import numpy as np
import json
from os import listdir
from os.path import isfile, join
from datetime import datetime

# from calculate_probability.poission_outcome_dist import prob_outcome
# from calculate_probability.calc_EV import calc_EV

from poission_outcome_dist import prob_outcome
from calc_EV import calc_EV


def calc_starting_xG(date, team, opp_team, gameIDs_played, player_df, lineups):
    res_xG = 0
    played_games = player_df[player_df["game_id"].isin(gameIDs_played)]
    
    # Get a list of the players starting the game
    #print(team)
    #print(date)
    players = lineups[(lineups["date"]==date) & (lineups["team_name"]==team)]
    if not players.empty:
        counter = 0
        for index, player in players.iterrows():
            #if player["pos"] != "Sub":
            tmp = played_games[played_games["name"]==player["player_name"]]
            if not tmp.empty:
                counter += 1
                res_xG += tmp["xg"].mean()

        if counter > 11:
            print(players)
            print(f"The number of starting players was wrong. Got {counter} instead of 11.")
            return None
        
    else:
        #print(f"[PROBLEM] Cant find which players that start the game for {team}.")
        return None

    return res_xG



def calc_game_prob(date, home_team, away_team, season_df, player_df, lineups):
    
    season_df["date"] = pd.to_datetime(season_df["date"])
    tmp = len(season_df)
    try:
        date = datetime.strptime(date, "%d %b %Y")
    except:
        return None

    played_games = season_df[season_df["date"] < date]
    min_num_games = 5
    if len(played_games[played_games["home_team"]==home_team]) < min_num_games and len(played_games[played_games["away_team"]==away_team]) < min_num_games:
        return None

    season_average_home_scored = played_games["hxg"].mean()
    season_average_home_conceded = played_games["axg"].mean()
    season_average_away_scored = played_games["axg"].mean()
    season_average_away_conceded = played_games["hxg"].mean()

    ### Find the average xG for the home and away teams starting players.
    gameIDs_played = played_games["game_id"].tolist()
    # Home team
    home_xG = calc_starting_xG(date, home_team, away_team, gameIDs_played, player_df, lineups)
    home_xG_conceded = played_games[played_games["home_team"]==home_team]["axg"].mean()
    # Away team
    away_xG = calc_starting_xG(date, away_team, home_team, gameIDs_played, player_df, lineups)
    away_xG_conceded = played_games[played_games["away_team"]==away_team]["hxg"].mean()

    if home_xG == None or away_xG == None:
        return None

    # print("A ", away_xG_conceded)
    # print("B ", season_average_away_conceded)
    # print(f"{home_xG/season_average_home_scored} * {(away_xG_conceded/season_average_away_conceded)} * {season_average_home_scored}")
    # print(f"{(away_xG/season_average_away_scored)} * {(home_xG_conceded/season_average_home_conceded)} * {season_average_away_scored}")

    HxG = (home_xG/season_average_home_scored) * (away_xG_conceded/season_average_away_conceded) * season_average_home_scored
    AxG = (away_xG/season_average_away_scored) * (home_xG_conceded/season_average_home_conceded) * season_average_away_scored

    res_prob = prob_outcome(HxG, AxG)
    return res_prob   


def generete_prediction(config):
    current_games_path = "./current_games/generated_data/"
    game_files = [f for f in listdir(current_games_path) if isfile(join(current_games_path, f))]
    
    # with open('./../config.cfg') as json_file:
    #     config = json.load(json_file)
    print("###### Game Predictions ######")
    for game in game_files:   
        if game not in ["PL_2021_only_old_games.csv", "SA_2021_only_old_games.csv"]:
            league = game.split("_")[2]
            season = game.split("_")[3]
            games_df = pd.read_csv(f"./prev_games/generated_data/{league}_{season}_games.csv", sep=";")
            games_df.sort_values(by="date", inplace=True)
            players_df = pd.read_csv(f"./prev_games/generated_data/{league}_{season}_players.csv", sep=";")
            date = game.split("_")[5]
            home_team = game.split("_")[4].split("-")[0]
            away_team = game.split("_")[4].split("-")[1]

            lineups = pd.read_csv(f"./lineups/generated_data/{league}_{season}_lineups.csv", sep=";")
            lineups["date"] = pd.to_datetime(lineups["date"])
            #lineups = pd.read_csv(f"./../lineups/generated_data/example.csv", sep=";")

            game_prob = calc_game_prob(date, home_team, away_team, games_df, players_df, lineups)
            #game_prob = {"HomeProb":0.60, "DrawProb":0.25, "AwayProb":0.15}
            if not game_prob == None:
                print("####################")
                print(f"Game {home_team} - {away_team} prob:")
                print(f"home: {game_prob['HomeProb']}\ndraw: {game_prob['DrawProb']}\naway: {game_prob['AwayProb']}")
                bet = calc_EV(game_prob, game, config)
                if bet != None:
                    print(f"Bet: {bet['Bet']} @{bet['Odds']} on {bet['Site']}.")
                print("####################")
    print("#####"*6)

def verify_old_games():
    league = "PL"
    season = "2021"
    df_old_games = pd.read_csv(f"./current_games/generated_data/{league}_{season}_only_old_games.csv", sep=";")
    lineups = pd.read_csv(f"./lineups/generated_data/{league}_{season}_lineups.csv", sep=";")
    lineups["date"] = pd.to_datetime(lineups["date"])
    games_df = pd.read_csv(f"./prev_games/generated_data/{league}_{season}_games.csv", sep=";")
    games_df.sort_values(by="date", inplace=True)
    players_df = pd.read_csv(f"./prev_games/generated_data/{league}_{season}_players.csv", sep=";")

    for index, row in df_old_games.iterrows():
        game_prob = calc_game_prob(row["date"], row["home_team"], row["away_team"], games_df, players_df, lineups)
        if not game_prob == None:
            df_old_games.at[index, "HomeProb"] = game_prob["HomeProb"]
            df_old_games.at[index, "DrawProb"] = game_prob["DrawProb"]
            df_old_games.at[index, "AwayProb"] = game_prob["AwayProb"]
            tmp = row["result"].split(":")
            df_old_games.at[index, "Result"] = "home" if (int(tmp[0])>int(tmp[1])) else ("draw" if int(tmp[0])==int(tmp[1]) else "away")
            tmp = [game_prob["HomeProb"], game_prob["DrawProb"], game_prob["AwayProb"]]
            tmp = tmp.index(max(tmp))
            df_old_games.at[index, "Prediction"] = "home" if (tmp==0) else ("draw" if tmp==1 else "away")
        else:
            df_old_games.at[index, "HomeProb"] = np.nan

    df_old_games.dropna(inplace=True)
    df_old_games.to_csv(f"./eval_old_games/{league}_{season}_eval.csv", index=False)


if __name__ == "__main__":
    verify_old_games()

