import logging
import pandas as pd
from typing import Type, Optional, Dict, Any

from nba_api.live.nba.endpoints import boxscore as live_boxscore, scoreboard
from nba_api.stats.endpoints import BoxScoreTraditionalV2 as static_boxscore

from ..data.models import BoxScoreData, StaticBoxScoreData, ScoreboardData

logger = logging.getLogger(__name__)

# Column mappings
PLAYER_STATS_COLUMNS_MAPPING = {
    'TEAM_ABBREVIATION': 'TEAM_ABBREVIATION',
    'PLAYER_NAME': 'name',
    'START_POSITION': 'position',
    'MIN': 'statistics_minutesCalculated',
    'PTS': 'statistics_points',
    'REB': 'statistics_reboundsTotal',
    'AST': 'statistics_assists',
    'STL': 'statistics_steals',
    'BLK': 'statistics_blocks',
    'TO': 'statistics_turnovers',
    'FGM': 'statistics_fieldGoalsMade',
    'FGA': 'statistics_fieldGoalsAttempted',
    'FG_PCT': 'statistics_fieldGoalsPercentage',
    'FG3M': 'statistics_threePointersMade',
    'FG3A': 'statistics_threePointersAttempted',
    'FG3_PCT': 'statistics_threePointersPercentage',
}

STATIC_PLAYER_STATS_COLUMNS = [
    'TEAM_ABBREVIATION', 'PLAYER_NAME', 'START_POSITION',
    'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO',
    'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT'
]

class NBAClient:
    """Client for interacting with NBA APIs."""

    @staticmethod
    def _fetch_and_parse(game_id: str, 
                         fetch_fn, 
                         parse_fn, 
                         model_cls: Type[Any]) -> Optional[Any]:
        """
        General method to fetch, parse and instantiate model.
        """
        try:
            raw_data = fetch_fn(game_id)
            parsed_data = parse_fn(raw_data)
            return model_cls(**parsed_data)
        except Exception as e:
            logger.error(f"[NBAClient] Error fetching {model_cls.__name__} for game {game_id}: {e}")
            return None

    @staticmethod
    def get_live_box_score(game_id: str) -> Optional[BoxScoreData]:
        return NBAClient._fetch_and_parse(
            game_id,
            NBAClient._fetch_live_data,
            NBAClient._parse_live_box_score,
            BoxScoreData
        )

    @staticmethod
    def get_static_box_score(game_id: str) -> Optional[StaticBoxScoreData]:
        return NBAClient._fetch_and_parse(
            game_id,
            NBAClient._fetch_static_data,
            NBAClient._parse_static_box_score,
            StaticBoxScoreData
        )
    
    @staticmethod
    def get_scoreboard() -> Optional[ScoreboardData]:
        return NBAClient._fetch_and_parse(
            game_id='',
            fetch_fn=NBAClient._fetch_scoreboard_data,
            parse_fn=NBAClient._parse_scoreboard_data,
            model_cls=ScoreboardData
        )

    @staticmethod
    def _fetch_live_data(game_id: str):
        return live_boxscore.BoxScore(game_id=game_id)

    @staticmethod
    def _fetch_static_data(game_id: str):
        return static_boxscore(game_id=game_id)

    @staticmethod
    def _fetch_scoreboard_data(game_id: str):
        return scoreboard.ScoreBoard()

    @staticmethod
    def _parse_live_box_score(data: live_boxscore.BoxScore) -> Dict[str, Any]:
        # Parse player stats
        home_players = data.home_team_player_stats.get_dict()
        away_players = data.away_team_player_stats.get_dict()
        home_df = pd.DataFrame(home_players)
        away_df = pd.DataFrame(away_players)

        home_df['TEAM_ABBREVIATION'] = data.home_team.get_dict()['teamTricode']
        away_df['TEAM_ABBREVIATION'] = data.away_team.get_dict()['teamTricode']

        all_players_df = pd.concat([home_df, away_df])

        player_stats_df = pd.json_normalize(all_players_df.to_dict('records'), sep='_')

        player_stats_clean = pd.DataFrame()
        for new_col, source_col in PLAYER_STATS_COLUMNS_MAPPING.items():
            player_stats_clean[new_col] = player_stats_df.get(source_col)

        # Parse team stats
        home_team_stats = data.home_team_stats.get_dict()
        away_team_stats = data.away_team_stats.get_dict()

        home_team_info = data.home_team.get_dict()
        away_team_info = data.away_team.get_dict()

        for stats, info in [(home_team_stats, home_team_info), (away_team_stats, away_team_info)]:
            stats['TEAM_ID'] = info['teamId']
            stats['TEAM_CITY'] = info['teamCity']
            stats['TEAM_NAME'] = info['teamName']
            stats['TEAM_ABBREVIATION'] = info['teamTricode']
            stats['TEAM_SCORE'] = info['score']

        # Game details
        game_details = data.game_details.get_dict()
        arena_info = data.arena.get_dict() if data.arena else {}

        return {
            'game_id': data.game_id,
            'game_status': game_details.get('gameStatusText', ''),
            'arena': arena_info,
            'player_stats': player_stats_clean.to_dict('records'),
            'team_stats': [home_team_stats, away_team_stats]
        }

    @staticmethod
    def _parse_static_box_score(data: static_boxscore) -> Dict[str, Any]:
        player_stats = data.player_stats.get_data_frame()
        team_stats = data.team_stats.get_data_frame()

        player_stats_clean = player_stats[STATIC_PLAYER_STATS_COLUMNS]

        return {
            'game_id': data.player_stats.get_data_frame()['GAME_ID'].iloc[0],
            'player_stats': player_stats_clean.to_dict('records'),
            'team_stats': team_stats.to_dict('records')
        }
    @staticmethod
    def _parse_scoreboard_data(data: scoreboard.ScoreBoard) -> Dict[str, Any]:
        # Parse scoreboard data
        return {
            'games': data.games.get_dict(),
            'game_date': data.score_board_date,
        }
