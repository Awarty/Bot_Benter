	
import pandas as pd
import numpy as np

from poission_outcome_dist import prob_outcome

def calc_starting_xG(game_id, team, gameIDs_played, player_df):
    if game_id in gameIDs_played:
        print("We have a problem of gameIDs leaking!!!")

    res_xG = 0
    played_games = player_df[player_df["game_id"].isin(gameIDs_played)]
    
    players = player_df[(player_df["game_id"]==game_id) & (player_df["team"]==team)]

    for index, player in players.iterrows():
        if player["pos"] != "Sub":
            tmp = played_games[played_games["name"]==player["name"]]
            if not tmp.empty:
                res_xG += tmp["xg"].mean()

    return res_xG



def calc_game_prob(game_info, season_df, player_df):
    """
        Calculates the probability distribution of a given game using xG and poission distribution.

        Input:
            - game_info
            panda row containing: "game_id", "home_team", "away_team", "fthg", "ftag", "hxg", "axg" and "date".
            - season_df
            contains all data for all teams this season. 
            - player_df
            contains all data for all players this season.

        Output:
            - returns a python dict with the probability distribution with the keys: "HomeProb", "DrawProb", "AwayProb".
    """

    played_games = season_df[season_df["date"] < game_info["date"]]

    season_average_home_scored = played_games["hxg"].mean()
    season_average_home_conceded = played_games["axg"].mean()
    season_average_away_scored = played_games["axg"].mean()
    season_average_away_conceded = played_games["hxg"].mean()

    ### Find the average xG for the home and away teams starting players.
    gameIDs_played = played_games["game_id"].tolist()
    # Home team
    home_xG = calc_starting_xG(game_info["game_id"], game_info["home_team"], gameIDs_played, player_df)
    home_xG_conceded = played_games[played_games["home_team"]==game_info["home_team"]]["axg"].mean()
    # Away team
    away_xG = calc_starting_xG(game_info["game_id"], game_info["away_team"], gameIDs_played, player_df)
    away_xG_conceded = played_games[played_games["away_team"]==game_info["away_team"]]["hxg"].mean()

    HxG = (home_xG/season_average_home_scored) * (away_xG_conceded/season_average_away_conceded) * season_average_home_scored
    AxG = (away_xG/season_average_away_scored) * (home_xG_conceded/season_average_home_conceded) * season_average_away_scored

    res_prob = prob_outcome(HxG, AxG)
    return res_prob   


games_df = pd.read_csv("./prev_games/generated_data/EPL_2021_games.csv", sep=";")
players_df = pd.read_csv("./prev_games/generated_data/EPL_2021_players.csv", sep=";")
games_df["date"] = pd.to_datetime(games_df["date"], format='%b %d %Y')
games_df.sort_values(by="date", inplace=True)

for index, row in games_df.iterrows():
    game_prob = calc_game_prob(row, games_df, players_df)
    print(row["home_team"], row["away_team"])
    print(row["fthg"], row["ftag"])
    print(game_prob)
    print("#############################")
    

