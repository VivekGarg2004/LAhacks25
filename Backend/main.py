import asyncio
from typing import List
from nba_api.live.nba.endpoints import scoreboard
from nba_stats.api.nba_client import NBAClient
import logging
from nba_stats.data.database import MongoDBClient

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 15
REFRESH_GAMES_INTERVAL_SECONDS = 300  # 5 minutes

# Shared cache
active_game_ids: List[str] = []

async def refresh_active_games_cache():
    """Refresh the cached list of active games every 5 minutes."""
    global active_game_ids
    while True:
        try:
            live_scoreboard = NBAClient.get_scoreboard()
            games = live_scoreboard.games
            active_game_ids = [
                game['gameId']
                for game in games
                if game.get('gameStatus', 0) == 2  # 2 = Live
            ]
            logger.info(f"Refreshed active games: {active_game_ids}")
        except Exception as e:
            print(f"Error refreshing active games: {e}")
        
        await asyncio.sleep(REFRESH_GAMES_INTERVAL_SECONDS)

async def update_live_games_loop():
    """Fetch and update box scores for cached active games every 15 seconds."""
    while True:
        try:
            if not active_game_ids:
                logger.info("No active games currently.")
            else:
                db_client = MongoDBClient()
                for game_id in active_game_ids:
                    logger.info(f"Refreshing box score for {game_id}")
                    box_score_data = NBAClient.get_live_box_score(game_id)
                    play_by_play_data = NBAClient.get_live_play_by_play(game_id)
                    if play_by_play_data:
                        print(f"Play-by-play data for game {game_id}: {play_by_play_data}")
                        if db_client.save(play_by_play_data, db_name="PlayByPlay", collection_name="play_by_play"):
                            logger.info(f"Live play-by-play data for game {game_id} successfully saved to MongoDB")
                        else:
                            logger.error(f"Failed to save live play-by-play data for game {game_id} to MongoDB")
                    if box_score_data:
                        if db_client.save(box_score_data, db_name="Boxscores", collection_name="live_boxscores"):
                            logger.info(f"Live box score for game {game_id} successfully saved to MongoDB")
                        else:
                            logger.error(f"Failed to live static box score for game {game_id} to MongoDB")
                    db_client.close()
        except Exception as e:
            print(f"Error updating box scores: {e}")
        
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def main():
    """Run both tasks concurrently."""
    await asyncio.gather(
        refresh_active_games_cache(),
        update_live_games_loop()
    )

def run_backend_live_updates():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down live updater cleanly...")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_backend_live_updates()
