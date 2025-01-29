def is_hand_complete(round_json):
    return round_json['state'].get('round_complete') is not None