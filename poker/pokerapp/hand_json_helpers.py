
def is_hand_complete(hand_json):
    return hand_json['state'].get('hand_complete') is not None

def current_player_user_id(hand_json):
    waiting_for_player = hand_json['state'].get('waiting_for_player_to_act')
    if not waiting_for_player:
        return None
    current_player_hand_index = waiting_for_player['player_index']
    current_player_user_id = hand_json['player_hands'][current_player_hand_index]['player']['id']
    return current_player_user_id

def is_players_turn(user_id, hand_json):
    current_player_id = current_player_user_id(hand_json)
    if not current_player_id:
        return False
    return str(user_id) == current_player_id

def pocket_cards_for_user(user_id, hand_json):
    for player_hand in hand_json['player_hands']:
        if player_hand['player']['id'] == str(user_id):
            return player_hand.get('pocket_cards', [])
    return []

def is_player_waiting_to_move(user_id, hand_json):
    if is_hand_complete(hand_json):
        return False
    if is_players_turn(user_id, hand_json):
        return False
    player_hands = hand_json['player_hands']
    for player_hand in player_hands:
        if player_hand['player']['id'] == str(user_id):
            if player_hand['status'] == 'in':
                return True
    return False

def is_player_in_hand(user_id, hand_json):
    player_hands = hand_json['player_hands']
    for player_hand in player_hands:
        if player_hand['player']['id'] == str(user_id):
            return player_hand['status'] == 'in'
    return False

def biggest_net_gain(hand_json):
    max_gain = 0
    player_user_id = None
    for player_hand in hand_json.get('player_hands', []):
        starting_chip_count = player_hand.get('starting_chip_count', 0)
        current_chip_count = player_hand['player'].get('chip_count', 0)
        net_gain = current_chip_count - starting_chip_count
        if net_gain > max_gain:
            max_gain = net_gain
            player_user_id = player_hand['player']['id']
    return (max_gain, player_user_id)

def get_players_with_net_gain(hand_json):
    players_with_net_gain = []

    # Loop through each player's hand to check for net gain
    for player_hand in hand_json.get('player_hands', []):
        starting_chip_count = player_hand.get('starting_chip_count', 0)
        current_chip_count = player_hand['player'].get('chip_count', 0)
        status = player_hand.get('status')
        
        net_gain = current_chip_count - starting_chip_count

        # If the net gain is positive, add the player to the result list
        if net_gain > 0 and status == 'in':
            players_with_net_gain.append({
                "player_id": player_hand['player']['id'],
                "name": player_hand['player']['name'],
                "net_gain": net_gain
            })

    return players_with_net_gain

def get_players_with_net_loss(hand_json):
    players_with_net_loss = []

    # Loop through each player's hand to check for net gain
    for player_hand in hand_json.get('player_hands', []):
        starting_chip_count = player_hand.get('starting_chip_count', 0)
        current_chip_count = player_hand['player'].get('chip_count', 0)
        status = player_hand.get('status')
        
        net_gain = current_chip_count - starting_chip_count

        # If the net gain is negative, add the player to the result list
        if net_gain < 0 and status == 'in':
            players_with_net_loss.append({
                "player_id": player_hand['player']['id'],
                "name": player_hand['player']['name'],
                "net_loss": abs(net_gain)
            })

    return players_with_net_loss

def calculate_total_pot_amount(hand_json):
    total_amount = 0.0
    for winner in hand_json.get("pot_winners", []):
        pot = winner.get("pot", {})
        total_amount += pot.get("amount", 0.0)
    return total_amount

def board_cards(hand_json):
    return hand_json.get('board', [])

def board_cards_to_string(board_cards, round):
    print("round: ", round, type(round))
    print("board_cards: ", board_cards)
    if round == 0:
        return ""
    elif round == 1:
        return ' '.join([card_to_string(card) for card in board_cards[:3]])
    elif round == 2:
        return ' '.join([card_to_string(card) for card in board_cards[:4]])
    return ' '.join([card_to_string(card) for card in board_cards])

def pocket_cards_to_string(pocket_cards):
    return card_to_string(pocket_cards['first']) + card_to_string(pocket_cards['second'])

def card_to_string(card):
    suit_symbols = {
        's': '♠️',  # Spades
        'c': '♣️',  # Clubs
        'd': '♦️',  # Diamonds
        'h': '♥️',  # Hearts
    }
    return f"{card['rank'].upper()}{suit_symbols[card['suit']]}"