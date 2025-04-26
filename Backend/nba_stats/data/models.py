import datetime
from typing import Dict, List, Any, Type, TypeVar, Optional

T = TypeVar('T', bound='BaseDataModel')

class BaseDataModel:
    """Base class for data models providing serialization helpers."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance attributes to a dictionary."""
        return self.__dict__

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        return cls(**data)

class BoxScoreData(BaseDataModel):
    """Data model for live box score information."""

    def __init__(self, 
                 game_id: str, 
                 game_status: str, 
                 arena: Dict[str, Any], 
                 player_stats: List[Dict[str, Any]], 
                 team_stats: List[Dict[str, Any]],
                 retrieved_at: Optional[datetime.datetime] = None):
        self.game_id = game_id
        self.game_status = game_status
        self.arena = arena
        self.player_stats = player_stats
        self.team_stats = team_stats
        self.retrieved_at = retrieved_at or datetime.datetime.now()

class StaticBoxScoreData(BaseDataModel):
    """Data model for static (historical) box score information."""

    def __init__(self, 
                 game_id: str, 
                 player_stats: List[Dict[str, Any]], 
                 team_stats: List[Dict[str, Any]],
                 retrieved_at: Optional[datetime.datetime] = None):
        self.game_id = game_id
        self.player_stats = player_stats
        self.team_stats = team_stats
        self.retrieved_at = retrieved_at or datetime.datetime.now()

class ScoreboardData(BaseDataModel):
    """Data model for NBA scoreboard information."""

    def __init__(self, 
                 game_date: str, 
                 games: List[Dict[str, Any]], 
                 retrieved_at: Optional[datetime.datetime] = None):
        self.game_date = game_date
        self.games = games
        self.retrieved_at = retrieved_at or datetime.datetime.now()