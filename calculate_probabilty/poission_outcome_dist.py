
import pandas as pd
import numpy as np
import math 


def prob_goals(num_goals, xG):
    a = math.pow(np.exp(1), -xG)
    b = math.pow(xG, num_goals)
    c = (a*b)/math.factorial(num_goals)
    return round(c, 4)

def prob_outcome(xG_home, xG_away):
    prob_home = 0
    prob_draw = 0
    prob_away = 0
    for i in range(6):
        for j in range(6):
            if i > j:
                prob_home += prob_goals(i, xG_home) * prob_goals(j, xG_away)
            if i == j:
                prob_draw += prob_goals(i, xG_home) * prob_goals(j, xG_away)
            if i < j:
                prob_away += prob_goals(i, xG_home) * prob_goals(j, xG_away)
    return {"HomeProb":round(prob_home, 4), "DrawProb":round(prob_draw, 4), "AwayProb":round(prob_away, 4)}




