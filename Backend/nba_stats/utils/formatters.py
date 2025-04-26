from ..data.models import BoxScoreData, StaticBoxScoreData, ScoreboardData, PlayByPlayData
from typing import Dict, List, Any, Set
from nba_api.stats.static import players
from dateutil import parser
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class BoxScoreFormatter:
    """Handles formatting of box score data for display"""
    
    @staticmethod
    def format_box_score(box_score_data: BoxScoreData) -> str:
        """Format box score data into a readable string"""
        output = []
        
        # Add game status
        output.append(f"\n===== GAME STATUS: {box_score_data.game_status} =====")
        
        # Add arena info if available
        if box_score_data.arena:
            arena = box_score_data.arena
            output.append(f"Arena: {arena.get('arenaName', 'N/A')} in {arena.get('arenaCity', 'N/A')}, {arena.get('arenaState', 'N/A')}")
        
        # Add team stats
        output.append("\n===== TEAM STATS =====")
        for team in box_score_data.team_stats:
            output.append(f"\n{team['TEAM_CITY']} {team['TEAM_NAME']} ({team['TEAM_ABBREVIATION']}): {team['TEAM_SCORE']} pts")
            
            fg_pct = team['statistics']['fieldGoalsPercentage']
            fg_pct_str = f"{fg_pct:.1%}" if isinstance(fg_pct, float) else "N/A"
            
            tp_pct = team['statistics']['threePointersPercentage']
            tp_pct_str = f"{tp_pct:.1%}" if isinstance(tp_pct, float) else "N/A"
            
            output.append(f"FG%: {fg_pct_str}, 3P%: {tp_pct_str}")
            output.append(f"Rebounds: {team['statistics']['reboundsTotal']}, " 
                         f"Assists: {team['statistics']['assists']}, "
                         f"Turnovers: {team['statistics'].get('turnoversTotal', 0)}")
        
        # Add player stats
        output.append("\n===== PLAYER STATS =====")
        team_abbrs = set(player['TEAM_ABBREVIATION'] for player in box_score_data.player_stats)
        
        for team_abbr in team_abbrs:
            team_players = [p for p in box_score_data.player_stats if p['TEAM_ABBREVIATION'] == team_abbr]
            output.append(f"\n{team_abbr} Players:")
            
            # Sort by points scored (highest first)
            for player in sorted(team_players, key=lambda x: x['PTS'], reverse=True):
                output.append(f"{player['PLAYER_NAME']} - {player['PTS']} pts, "
                             f"{player['REB']} reb, {player['AST']} ast, {player['MIN']} min")
        
        return "\n".join(output)
    
    @staticmethod
    def print_box_score(box_score_data: BoxScoreData) -> None:
        """Print formatted box score to console"""
        formatted_output = BoxScoreFormatter.format_box_score(box_score_data)
        print(formatted_output)
    
    @staticmethod
    def format_static_box_score(box_score_data: StaticBoxScoreData) -> str:
        """Format static box score data into a readable string"""
        output = []
        
        # Add team stats
        output.append("\n===== TEAM STATS =====")
        for team in box_score_data.team_stats:
            output.append(f"\n{team['TEAM_CITY']} {team['TEAM_NAME']} ({team['TEAM_ABBREVIATION']})")
            
            # Format percentages
            fg_pct = team['FG_PCT']
            fg_pct_str = f"{fg_pct:.1%}" if isinstance(fg_pct, float) else "N/A"
            
            fg3_pct = team['FG3_PCT']
            fg3_pct_str = f"{fg3_pct:.1%}" if isinstance(fg3_pct, float) else "N/A"
            
            output.append(f"Points: {team['PTS']}, FG%: {fg_pct_str}, 3P%: {fg3_pct_str}")
            output.append(f"Rebounds: {team['REB']}, Assists: {team['AST']}, Turnovers: {team['TO']}")
        
        # Add player stats
        output.append("\n===== PLAYER STATS =====")
        team_abbrs = set(player['TEAM_ABBREVIATION'] for player in box_score_data.player_stats)
        
        for team_abbr in team_abbrs:
            team_players = [p for p in box_score_data.player_stats if p['TEAM_ABBREVIATION'] == team_abbr]
            output.append(f"\n{team_abbr} Players:")
            
            # Sort by points scored (highest first)
            for player in sorted(team_players, key=lambda x: x['PTS'], reverse=True):
                output.append(f"{player['PLAYER_NAME']} - {player['PTS']} pts, "
                             f"{player['REB']} reb, {player['AST']} ast, {player['MIN']} min")
        
        return "\n".join(output)
    
    @staticmethod
    def print_static_box_score(box_score_data: StaticBoxScoreData) -> None:
        """Print formatted static box score to console"""
        formatted_output = BoxScoreFormatter.format_static_box_score(box_score_data)
        print(formatted_output)
    
class ScoreboardFormatter:
    """Handles formatting of scoreboard data for display"""
    @staticmethod
    def format_scoreboard(scoreboard_data: ScoreboardData) -> str:
        """Format scoreboard data into a readable string"""
        output = []
        
        # Add scoreboard header
        output.append("\n===== NBA SCOREBOARD =====")
        logger.info("Formatting scoreboard data")
        f = "{gameId}: {awayTeam} vs. {homeTeam} @ {gameTimeLTZ}" 
        
        # Add game status
        
        for game in scoreboard_data.games:
            gameTimeLTZ = parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None)
            output.append(f.format(gameId=game['gameId'], 
                                    awayTeam=game['awayTeam']['teamName'], 
                                    homeTeam=game['homeTeam']['teamName'], 
                                    gameTimeLTZ=gameTimeLTZ))
            

        
        return "\n".join(output)
    @staticmethod
    def print_scoreboard(scoreboard_data: Dict[str, Any]) -> None:
        """Print formatted scoreboard to console"""
        logger.info("Printing formatted scoreboard")
        formatted_output = ScoreboardFormatter.format_scoreboard(scoreboard_data)
        print(formatted_output)

class PlayByPlayFormatter:
    """Handles formatting of play-by-play data for display"""
    
    @staticmethod
    def format_play_by_play(play_by_play_data: PlayByPlayData) -> str:
        """Format play-by-play data into a readable string"""
        output = []
        line = "{action_number}: {period}:{clock} {player_id} ({action_type})"
        
        # Add play-by-play header
        output.append("\n===== PLAY-BY-PLAY =====")
        
        # Add each play
        for play in play_by_play_data.plays:
            player_name = ''
            player = players.find_player_by_id(play['personId'])
            if player is not None:
                player_name = player['full_name']
            output.append(line.format(action_number=play['actionNumber'],period=play['period'],clock=play['clock'],action_type=play['description'],player_id=player_name))
        return "\n".join(output)
    
    @staticmethod
    def print_play_by_play(play_by_play_data: List[Dict[str, Any]]) -> None:
        """Print formatted play-by-play to console"""
        formatted_output = PlayByPlayFormatter.format_play_by_play(play_by_play_data)
        print(formatted_output[:1000])  # Limit to first 1000 characters for readability