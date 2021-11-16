	
import pandas as pd
import numpy as np




def calc_EV(game_prob, game_file, config):
    game_odds = pd.read_csv("./../current_games/generated_data/" + game_file, sep=";")
    game_odds = game_odds[game_odds["Site"].isin(config["betting"]["whitelisted_betting_sites"])]
    
    if not game_odds.empty:
        home_odds = game_odds[game_odds.index == game_odds["Home"].idxmax()]
        draw_odds = game_odds[game_odds.index == game_odds["Draw"].idxmax()]
        away_odds = game_odds[game_odds.index == game_odds["Away"].idxmax()]

        home_EV = (game_prob["HomeProb"] * (home_odds["Home"].values[0]-1)) - ((1-game_prob["HomeProb"]) * 1)
        draw_EV = (game_prob["DrawProb"] * (draw_odds["Draw"].values[0]-1)) - ((1-game_prob["DrawProb"]) * 1)
        away_EV = (game_prob["AwayProb"] * (away_odds["Away"].values[0]-1)) - ((1-game_prob["AwayProb"]) * 1)

        if home_EV > draw_EV and home_EV > away_EV and home_EV >= config["betting"]["bet_strategy"]["EV"]["min_edge"]:
            # Bet on home 
            print(home_odds)  
            return {"Site":home_odds["Site"].values[0], "Bet": "Home", "Odds":home_odds["Home"].values[0]}

        if draw_EV > home_EV and draw_EV > away_EV and draw_EV >= config["betting"]["bet_strategy"]["EV"]["min_edge"]:
            # Bet on draw 
            return {"Site":draw_odds["Site"].values[0], "Bet": "Draw", "Odds":draw_odds["Draw"].values[0]}

        if away_EV > draw_EV and away_EV > home_EV and away_EV >= config["betting"]["bet_strategy"]["EV"]["min_edge"]:
            # Bet on away 
            return {"Site":away_odds["Site"].values[0], "Bet": "Away", "Odds":away_odds["Away"].values[0]}

    else:
        print("No betting information for this game.")

    return None



