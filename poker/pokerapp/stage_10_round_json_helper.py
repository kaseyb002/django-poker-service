def is_round_complete(round_json):
    return round_json['state'].get('round_complete') is not None

def current_player_user_id(round_json):
    waiting_for_player = round_json['state'].get('waiting_for_player_to_act')
    if not waiting_for_player:
        return None
    current_player_user_id = waiting_for_player['player_id']
    return current_player_user_id

def is_players_turn(user_id, round_json):
    current_player_id = current_player_user_id(round_json)
    if not current_player_id:
        return False
    return str(user_id) == current_player_id
