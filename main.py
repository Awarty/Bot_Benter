import prev_games.prev_games as prev_games
import current_games.current_games as current_games
import lineups.lineups as lineups
import calculate_probability.calc_prob as calc_prob
import json


if __name__ == "__main__":
    # Read json from file ./../config.cfg
    with open('./config.cfg') as json_file:
        config = json.load(json_file)

    print("Running prev_games")
    #prev_games.generate_prev_games_data_files(config)

    print("Running current_games")
    current_games.generate_current_games_data_files(config)

    print("Running lineups")
    #lineups.generate_lineups_data_files(config)

    print("Please run probas you'r self, or if you are Alumnroot pls fix you'r code...")
    #calc_prob.generate_probability_data_files(config)
    calc_prob.generete_prediction(config)
    
