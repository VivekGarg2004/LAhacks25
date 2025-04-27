from construct_boxscore_main import construct_box_score
from play_by_play_main import process_play_by_play

construct_box_score('0022200001', 0, 7200)
process_play_by_play(game_id='0022200001', save_to_db=False)