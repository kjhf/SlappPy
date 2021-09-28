from dataclasses import dataclass


@dataclass
class BattlefyPlayer:
    in_game_name: str
    user_slug: str

    @staticmethod
    def from_dict(obj: dict) -> 'BattlefyPlayer':
        assert isinstance(obj, dict)
        return BattlefyPlayer(
            in_game_name=obj.get("inGameName", None),
            user_slug=obj.get("userSlug", None)
        )

    def to_dict(self) -> dict:
        result = {"inGameName": self.in_game_name, "userSlug": self.user_slug}
        return result
