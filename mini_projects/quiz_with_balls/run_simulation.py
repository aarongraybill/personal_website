import numpy as np
import math

# Create a version of nPk that doesn't do more computation than necessary
def nPk(n: int, k: int) -> int:
  # uses a ternary expression to return 0 if trying to choose more than available
  return np.prod(range(n-k+1,n+1)) if k<=n else 0

def f(j: int, p: int, b: int) -> float:
  numerator = math.comb(p,j) * nPk(p, j) * nPk(b-p,p-j)
  denominator = nPk(b,p)
  return (numerator/denominator)

f(4,5,6)

from string import ascii_uppercase
from numpy.random import choice
import pandas as pd

class Team:
  
  def __init__(self, n_balls: int, name: str = None):
    
    self.finished = False
    
    self.n_balls = n_balls
    
    self.name = name
    if self.name is None:
      # if no name was given, make it a random string
      self.name = ''.join(choice(ascii_uppercase) for i in range(6))
  
    self.players = self.n_balls - 1
    self.points = 0
  
    self.player_history = [self.players]
    self.point_history = [self.points]
    
    # for each combination of j and p, compute the probability
    x = [f(j,p,self.n_balls) for j in range(self.n_balls) for p in range(self.n_balls)]
    
    # convert the 1D array of probabilities to a matrix
    # and transpose so indexes are as expected
    self.M = np.reshape(x, (-1,self.n_balls)).T
  
  def play_round(self, round_number: int):
    
    # If not finished, run a simulation
    if not self.finished:
      probs = self.M[self.players, :]
      
      self.players = np.random.choice(range(self.n_balls),1,p=probs)[0]
      self.points += round_number * self.players
      # If you're ending the round with zero players, you're finished
      if self.players == 0:
        self.finished = True
    
    # Either way, append info to the history
    self.player_history.append(self.players)
    self.point_history.append(self.points)
      
    return (self.players, self.points)
  
  def rig_round(self, round_number, n_correct):
    assert self.players >= n_correct
    # If not finished, rig this round
    if not self.finished:
      
      self.players = n_correct
      self.points += round_number * self.players
      # If you're ending the round with zero players, you're finished
      if self.players == 0:
        self.finished = True
    
    # Either way, append info to the history
    self.player_history.append(self.players)
    self.point_history.append(self.points)
    
  def summarize(self):
    out = {
      'name' : self.name,
      'players': self.players,
      'points': self.points
      }
      
    return out
  
class Game:
  def __init__(self, n_balls=6, n_teams=2):
    assert n_teams <= 26 # needed for team naming
    self.n_balls = n_balls
    self.n_teams = n_teams
    self.finished = False
    self.round_number = 1
    self.winner = None
    self.teams = [Team(self.n_balls, name = ascii_uppercase[i]) for i in range(self.n_teams)]
    
  def is_finished(self):
    finished_teams = np.sum([t.finished for t in self.teams])
    one_remaining = finished_teams >= (self.n_teams - 1)
    out_of_turns = self.round_number > 5
    # The game is over as soon as there is only one team not 
    # finished
    return one_remaining | out_of_turns
  
  def play(self):
    
    #while self.finished is False:
    while not self.finished:
      # Keep playing until all teams are out
      [t.play_round(self.round_number) for t in self.teams]
      self.round_number += 1
      self.finished = self.is_finished()

    # Print score at end of game
    scores = [t.points for t in self.teams]
    
    # Test to see if it's not a tie
    if any(scores[0]!=scores[1:]):
      self.winner = np.argmax(scores)
      return None
  
  def summarize_game(self):
    x = [t.summarize() for t in self.teams]
    df = pd.DataFrame(x)
    df['won'] = [self.winner == i for i, _ in enumerate(self.teams)]
    df['round'] = self.round_number
    return df


def simulate(n: int = 10000, WorkingGame = Game):
  summaries = []
  for i in range(n):
    g = WorkingGame()
    g.play()
    df = g.summarize_game()
    df['game_no'] = i
    summaries.append(df)
    
  df = pd.concat(summaries)
  # make sure index isn't duplicated
  df = df.reset_index(drop = True)
  
  df['rigging'] = WorkingGame.__name__

  return df

np.random.seed(0)
df = simulate(n=10000)

df.to_csv('unfavored.csv', index = False)

# Create a class inheriting from the standard game 
class FavorA(Game):
  def __init__(self):
    # Creates the unbiased game
    super().__init__()
    # Override the first round to favor A
    self.teams[0].rig_round(1,5)
    self.teams[1].rig_round(1,4)
    self.round_number = 2

# Run simulation favoring A
np.random.seed(1)
df = simulate(n=10000, WorkingGame = FavorA)

df.to_csv('favor_a.csv', index = False)

prob_favor = 1 - (f(5,5,6)**2) - (f(4,5,6)**2)
prob_favor = round(100*prob_favor, 2)

final_prob = round(prob_favor * float(r.lower_bound) / 100.0,2)

assert final_prob > 25
