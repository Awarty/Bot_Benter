	
import pandas as pd
import numpy as np
import json
from os import listdir
from os.path import isfile, join
from datetime import datetime

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

        if counter != 11:
            print(f"The number of starting players was wrong. Got {counter} instead of 11.")
            return None
        
    else:
        #print(f"[PROBLEM] Cant find which players that start the game for {team}.")
        return None

    return res_xG



def calc_game_prob(date, home_team, away_team, season_df, player_df, lineups):
    
    season_df["date"] = pd.to_datetime(season_df["date"])
    tmp = len(season_df)
    date = datetime.strptime(date, "%d %b %Y")
    played_games = season_df[season_df["date"] < date]
    if tmp != len(played_games):
        print("Have problem with pre_game containing information from future games???")
    


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


if __name__ == "__main__":
    current_games_path = "./../current_games/generated_data/"
    game_files = [f for f in listdir(current_games_path) if isfile(join(current_games_path, f))]
    
    with open('./../config.cfg') as json_file:
        config = json.load(json_file)
    
    for game in game_files:                
        league = game.split("_")[0]
        season = game.split("_")[1]
        games_df = pd.read_csv(f"./../prev_games/generated_data/{league}_{season}_games.csv", sep=";")
        games_df.sort_values(by="date", inplace=True)
        players_df = pd.read_csv(f"./../prev_games/generated_data/{league}_{season}_players.csv", sep=";")
        date = game.split("_")[3]
        home_team = game.split("_")[2].split("-")[0]
        away_team = game.split("_")[2].split("-")[1]

        lineups = pd.read_csv(f"./../lineups/generated_data/{league}_{season}_lineups.csv", sep=";")
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

