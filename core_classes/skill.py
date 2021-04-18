import json
from typing import Optional, Iterable, List, Tuple

import trueskill
from trueskill import Rating, expose, global_env

SCALAR = 60  # Brings the clout to 3000 range.

# Setup the TrueSkill environment.
print("Initialising TrueSkill ...")
trueskill.setup()


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

    def to_dict(self) -> dict:
        return {"μ": self.rating.mu, "σ": self.rating.sigma}

    def __str__(self):
        return json.dumps(
            {"clout": self.clout, "confidence": self.confidence, "μ": self.rating.mu, "σ": self.rating.sigma}
        )

    @property
    def is_default(self) -> bool:
        """Return if the Skill object is at defaults"""
        return (global_env().mu == self.rating.mu
                and global_env().sigma == self.rating.sigma)

    @property
    def clout(self) -> int:
        """
        Return a public-facing estimation of the skill rating.
        This is the (conservative) min-rating clout
        or 2 sigmas below current actual
        """
        return int(expose(self.rating) * SCALAR)

    @property
    def confidence(self) -> int:
        """Return a public-facing confidence in % of how accurate the clout is"""
        return int(self.rating.pi * 100)

    @property
    def message(self) -> str:
        """Return a public-facing message describing the clout and confidence"""
        return Skill.make_message_clout(self.clout, self.confidence)

    def set_to_default(self):
        """Reset the player's rating to default."""
        self.rating = Rating()

    @staticmethod
    def make_message_clout(clout: int, clout_confidence: int, name: Optional[str] = None):
        """Get a message indicating the clout represented by the clout and confidence."""
        subject_name = name + " is" if name else 'They are'
        object_name = name if name else 'them'

        return (
            f"I have literally nothing on {object_name}." if clout_confidence == 0 else
            f"I don't know anything about {object_name} yet. ({clout_confidence}% confidence)" if clout_confidence < 2 else
            f"I don't know enough about {object_name} yet. Here's a *really* rough figure: {clout} ({clout_confidence}% confidence)" if clout_confidence < 5 else
            f"Early indications suggest {clout} clout for {object_name}. Really not sure about it. ({clout_confidence}% confidence)" if clout_confidence < 10 else
            f"Maybe {clout} clout for {object_name} but I'm not sure about it. ({clout_confidence}% confidence)" if clout_confidence < 33 else
            f"I'll say {clout} clout for {object_name} but I'm uncertain. ({clout_confidence}% confidence)" if clout_confidence < 50 else
            f"{subject_name} about {clout} clout, maybe. ({clout_confidence}% confidence)" if clout_confidence < 60 else
            f"I'd put {object_name} at {clout} clout, give or take. ({clout_confidence}% confidence)" if clout_confidence < 67 else
            f"{subject_name} about {clout} clout, fairly sure. ({clout_confidence})% confidence)" if clout_confidence < 80 else
            f"I'd rate {object_name} at {clout} clout. ({clout_confidence}% confidence)" if clout_confidence < 90 else
            f"{subject_name} {clout} clout. ({clout_confidence}%  confidence)"
        )

    @staticmethod
    def make_message_fairness(chance: int):
        """Get a message indicating the fairness represented by the chance parameter."""
        return (
            f"Looks like a slaughterhouse. ({chance}% chance of fair game)" if chance < 5 else
            f"Wow that is a horrifyingly unbalanced game. ({chance}% chance of fair game)" if chance < 10 else
            f"Seems unfair to me. ({chance}% chance of fair game)" if chance < 33 else
            f"I wonder if our underdogs could cause an upset. ({chance}% chance of fair game)" if chance < 50 else
            f"Could be an okay game to learn from. ({chance}% chance of fair game)" if chance < 60 else
            f"Could be a fun game. ({chance}% chance of fair game)" if chance < 67 else
            f"Looks good. ({chance}% chance of fair game)" if chance < 80 else
            f"I'd be interested to see this game. ({chance}% chance of fair game)" if chance < 90 else
            f"I've no idea which way this would go! ({chance}% chance of fair game)"
        )

    @staticmethod
    def from_dict(obj: dict) -> 'Skill':
        if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], dict):
            obj = obj[0]

        assert isinstance(obj, dict), f"Failed dict assertion: {obj}"
        return Skill(
            rating=Rating(
                mu=obj.get("μ") if "μ" in obj else None,
                sigma=obj.get("σ") if "σ" in obj else None
            )
        )

    @staticmethod
    def team_clout(team_skills: Iterable['Skill']) -> ((int, int), (int, int)):
        """Get a clout of a group of skills. Returns a tuple of ((minimum, confidence), (maximum, confidence))."""
        min_group = Skill._get_minimum_clout_team_skills(team_skills)
        max_group = Skill._get_maximum_clout_team_skills(team_skills)

        minimum_list = [skill.clout for skill in min_group]
        if len(minimum_list):
            minimum = sum(minimum_list) / len(minimum_list)
            minimum_list = [skill.confidence for skill in min_group]
            minimum_confidence = sum(minimum_list) / len(minimum_list)
        else:
            minimum = 0
            minimum_confidence = 0

        maximum_list = [skill.clout for skill in max_group]
        if len(maximum_list):
            maximum = sum(maximum_list) / len(maximum_list)
            maximum_list = [skill.confidence for skill in max_group]
            maximum_confidence = sum(maximum_list) / len(maximum_list)
        else:
            maximum = 0
            maximum_confidence = 0

        return (int(minimum), int(minimum_confidence)), (int(maximum), int(maximum_confidence))

    @staticmethod
    def calculate_quality_of_game_players(player1: 'Skill', player2: 'Skill') -> int:
        """
        Calculate the quality of the game, which is the likelihood of the game being a draw (evenly balanced).
        Returns a percentage.
        """
        return int(trueskill.quality_1vs1(player1.rating, player2.rating) * 100)

    @staticmethod
    def calculate_quality_of_game_teams(team1: Iterable['Skill'], team2: Iterable['Skill']) -> (int, int):
        """
        Calculate the quality of the game, which is the likelihood of the game being a draw (evenly balanced).

        Returns a tuple of ints -- percentages,
          - The first being the quality if team1 has their best roster on and team2 has their worst,
          - The second being the quality if team1 has their worst roster on and team2 has their best.
        """
        favouring_team1 = trueskill.quality(rating_groups=[Skill._get_maximum_clout_team_rating_group(team1),
                                                           Skill._get_minimum_clout_team_rating_group(team2)])
        favouring_team2 = trueskill.quality(rating_groups=[Skill._get_minimum_clout_team_rating_group(team1),
                                                           Skill._get_maximum_clout_team_rating_group(team2)])
        return int(favouring_team1 * 100), int(favouring_team2 * 100)

    @staticmethod
    def _get_minimum_clout_team_skills(team_players_skills: Iterable['Skill']) -> List['Skill']:
        """Filter the incoming Skills iterable to feature the 4 worst and return as a list."""
        result = list(team_players_skills)
        result.sort()
        return result[0:min(4, len(result))]

    @staticmethod
    def _get_minimum_clout_team_rating_group(team_players_skills: Iterable['Skill']) -> Tuple[Rating, ...]:
        """Filter the incoming Skills iterable to feature the 4 worst and return as ratings tuples."""
        return _as_rating_groups(Skill._get_minimum_clout_team_skills(team_players_skills))

    @staticmethod
    def _get_maximum_clout_team_skills(team_players_skills: Iterable['Skill']) -> List['Skill']:
        """Filter the incoming Skills iterable to feature the 4 worst and return as a list."""
        result = list(team_players_skills)
        result.sort(reverse=True)
        return result[0:min(4, len(result))]

    @staticmethod
    def _get_maximum_clout_team_rating_group(team_players_skills: Iterable['Skill']) -> Tuple[Rating, ...]:
        """Filter the incoming Skills iterable to feature the 4 worst and return as ratings tuples."""
        return _as_rating_groups(Skill._get_maximum_clout_team_skills(team_players_skills))

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
                               weights=[team1_weights, team2_weights])

        for i in range(0, len(teams[0])):
            team1[i].rating = teams[0][i]

        for i in range(0, len(teams[1])):
            team2[i].rating = teams[1][i]

    @staticmethod
    def from_division(normalised_value: int) -> 'Skill':
        # TODO -- the following code seeds off of divs but it's way better to work out skill by games ...
        # from core_classes.division import DIVISION_UNKNOWN_VAL
        # if normalised_value != DIVISION_UNKNOWN_VAL and normalised_value < 9:
        #     return Skill(rating=global_env().create_rating(mu=(9 - normalised_value) * trueskill.MU))
        # else:
        #     return Skill()
        return Skill()


def _as_rating_groups(skills: Iterable[Skill]) -> tuple:
    """Transform an iterable of skills into rating tuples for use in the trueskill module."""
    return tuple([skill.rating for skill in skills])
