from typing import Optional, Iterable, List

import trueskill
from trueskill import Rating, expose, global_env

MU = 1500
SIGMA = 500.0  # MU/3
BETA = 250.0  # SIGMA / 2
TAU = 5.0  # SIGMA / 100
DRAW_PROBABILITY = 0.0
DELTA = 0.006


class Skill:
    def __init__(self,
                 rating: Optional[Rating] = None):
        self.rating: rating = rating or Rating()

    def __lt__(self, other): return self.clout < other.clout
    def __le__(self, other): return self.clout <= other.clout
    def __eq__(self, other): return self.clout == other.clout
    def __ne__(self, other): return self.clout != other.clout
    def __gt__(self, other): return self.clout > other.clout
    def __ge__(self, other): return self.clout >= other.clout

    @staticmethod
    def from_dict(obj: dict) -> 'Skill':
        assert isinstance(obj, dict)
        return Skill(
            rating=Rating(
                mu=obj.get("μ") if "μ" in obj else None,
                sigma=obj.get("σ") if "σ" in obj else None
            )
        )

    def to_dict(self) -> dict:
        result = {}
        if not self.is_default:
            result["μ"] = self.rating.mu
            result["σ"] = self.rating.sigma
        return result

    @property
    def is_default(self) -> bool:
        """Return if the Skill object is at defaults"""
        return (global_env().mu == self.rating.mu
                and global_env().sigma == self.rating.sigma)

    @property
    def clout(self) -> float:
        """Return a public-facing estimation of the skill rating"""
        return expose(self.rating)

    @staticmethod
    def team_clout(team_skills: Iterable['Skill']) -> (float, float):
        """Get a clout of a group of skills. Returns a tuple of (minimum, maximum)."""
        return (Skill.get_minimum_clout_team_rating_group(team_skills),
                Skill.get_maximum_clout_team_rating_group(team_skills))

    @staticmethod
    def calculate_quality_of_game(team1: Iterable['Skill'], team2: Iterable['Skill']) -> (float, float):
        """
        Calculate the quality of the game, which is the likelihood of the game being a draw (evenly balanced).

        Returns a tuple of floats,
          - The first being the quality if team1 has their best roster on and team2 has their worst,
          - The second being the quality if team1 has their worst roster on and team2 has their best.
        """
        favouring_team1 = trueskill.quality(rating_groups=[Skill.get_maximum_clout_team_rating_group(team1),
                                                           Skill.get_minimum_clout_team_rating_group(team2)])
        favouring_team2 = trueskill.quality(rating_groups=[Skill.get_minimum_clout_team_rating_group(team1),
                                                           Skill.get_maximum_clout_team_rating_group(team2)])
        return favouring_team1, favouring_team2

    @staticmethod
    def get_minimum_clout_team_rating_group(team_players_skills: Iterable['Skill']) -> tuple:
        """Filter the incoming Skills iterable to feature the 4 worst and return as a tuple."""
        result = list(team_players_skills)
        result.sort()
        return tuple(result[0:4])

    @staticmethod
    def get_maximum_clout_team_rating_group(team_players_skills: Iterable['Skill']) -> tuple:
        """Filter the incoming Skills iterable to feature the 4 worst and return as a tuple."""
        result = list(team_players_skills)
        result.sort(reverse=True)
        return tuple(result[0:4])

    @staticmethod
    def setup():
        """Setup the TrueSkill environment."""
        print("Initialising TrueSkill ...")
        trueskill.setup(mu=MU,
                        sigma=SIGMA,
                        beta=BETA,
                        tau=TAU,
                        draw_probability=DRAW_PROBABILITY)

    @staticmethod
    def calculate_and_adjust_2v2(team1: List['Skill'], team2: List['Skill'], did_team_1_win: bool):
        """Calculates and adjusts a 2v2 game."""
        Skill.calculate_and_adjust(2, team1, team2, did_team_1_win)

    @staticmethod
    def calculate_and_adjust_4v4(team1: List['Skill'], team2: List['Skill'], did_team_1_win: bool):
        """Calculates and adjusts a 4v4 game."""
        Skill.calculate_and_adjust(4, team1, team2, did_team_1_win)

    @staticmethod
    def calculate_and_adjust(players_per_side: int, team1: List['Skill'], team2: List['Skill'], did_team_1_win: bool):
        """Calculates and adjusts a game."""

        ranks = [0, 1] if did_team_1_win else [1, 0]

        # Apply a weighting based on the number of players in the roster.
        # This way, the game is always kept "fair" as if each player is subbed out at regular intervals.
        if len(team1) < players_per_side:
            team1_weights = (1,) * len(team1)
        else:
            team1_weights = (players_per_side / len(team1),) * len(team1)

        if len(team2) < players_per_side:
            team2_weights = (1,) * len(team2)
        else:
            team2_weights = (players_per_side / len(team2),) * len(team2)

        teams = trueskill.rate(rating_groups=[tuple([t1.rating for t1 in team1]),
                                              tuple([t2.rating for t2 in team2])],
                               ranks=ranks,
                               weights=[team1_weights, team2_weights],
                               min_delta=DELTA)

        for i in range(0, len(teams[0])):
            team1[i].rating = teams[0][i]

        for i in range(0, len(teams[1])):
            team2[i].rating = teams[1][i]
