BIG_POT = "BIG_POT"
I_WAS_FORCED_MOVED = "I_WAS_FORCED_MOVED"
I_WAS_SAT_OUT = "I_WAS_SAT_OUT"
I_WAS_REMOVED_FROM_TABLE = "I_WAS_REMOVED_FROM_TABLE"
MY_CHIPS_ADJUSTED = "MY_CHIPS_ADJUSTED"
NEW_MEMBER_JOINED = "NEW_MEMBER_JOINED"
IS_MY_TURN = "IS_MY_TURN"
NEW_CHAT_MESSAGE = "NEW_CHAT_MESSAGE"
I_LOST_HAND = "I_LOST_HAND"
I_WON_HAND = "I_WON_HAND"

def chat_room_id(table_id):
    return f"table_{table_id}"

def game_thread_id(game_id):
    return f"game_{game_id}"

def game_collapse_id(game_id):
    return f"game_{game_id}"