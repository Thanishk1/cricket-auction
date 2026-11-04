from flask import Flask, jsonify, request, render_template
from models import generate_players, place_bid, buy_player, Player, Team
import time

app = Flask(__name__)

game_state = {
    "players": [],
    "current_player": None,
    "team_a": None,
    "team_b": None,
    "current_highest_bid": 0,
    "current_winning_team": None,
    "current_turn": None,
    "turn_started_at": None,
    "no_of_passes": 0   # ADDED: tracks consecutive declines this round
}

TIMEOUT_DURATION = 10


def check_timeout():
    if game_state["turn_started_at"] is None or game_state["current_turn"] is None:
        return None

    elapsed_time = time.time() - game_state["turn_started_at"]
    if elapsed_time > TIMEOUT_DURATION:
        timed_out_team = game_state["current_turn"]
        if timed_out_team == game_state["team_a"].name:
            winning_team = game_state["team_b"]
        else:
            winning_team = game_state["team_a"]

        sold_player = game_state["current_player"]
        sold_price = game_state["current_highest_bid"]
        buy_player(sold_player, winning_team, sold_price)

        game_state["current_highest_bid"] = 0
        game_state["current_winning_team"] = None
        game_state["current_turn"] = None
        game_state["turn_started_at"] = None
        game_state["no_of_passes"] = 0

        if game_state["players"]:
            game_state["current_player"] = game_state["players"].pop(0)
        else:
            game_state["current_player"] = None

        return f"{timed_out_team} timed out. {winning_team.name} wins the bid for {sold_player.name} for {sold_price}."

    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start')
def start_game():
    game_state["players"] = generate_players(10)
    game_state["team_a"] = Team(name="You", players=[], slots_to_fill=5, total_amount=50, remaining_amount=50)
    game_state["team_b"] = Team(name="Bot", players=[], slots_to_fill=5, total_amount=50, remaining_amount=50)
    game_state["current_highest_bid"] = 0
    game_state["current_winning_team"] = None
    game_state["current_turn"] = None
    game_state["turn_started_at"] = None
    game_state["no_of_passes"] = 0
    game_state["current_player"] = game_state["players"].pop(0)

    players_data = [{"name": p.name, "season": p.season} for p in game_state["players"]]
    return jsonify({
        "message": "Game started!",
        "players": players_data,
        "current_player": {"name": game_state["current_player"].name, "season": game_state["current_player"].season},
        "team_a": {"name": game_state["team_a"].name, "remaining_amount": game_state["team_a"].remaining_amount, "Players": []},
        "team_b": {"name": game_state["team_b"].name, "remaining_amount": game_state["team_b"].remaining_amount, "Players": []}
    })


@app.route('/status', methods=['GET'])
def status():
    timeout_message = check_timeout()

    seconds_remaining = None
    if game_state["current_turn"] is not None and game_state["turn_started_at"] is not None:
        elapsed = time.time() - game_state["turn_started_at"]
        seconds_remaining = max(0, round(TIMEOUT_DURATION - elapsed))

    team_a = game_state["team_a"]
    team_b = game_state["team_b"]
    remaining_money_a = team_a.remaining_amount if team_a else None
    remaining_money_b = team_b.remaining_amount if team_b else None
    return jsonify({
        "timeout_event": timeout_message,
        "current_player": {"name": game_state["current_player"].name, "season": game_state["current_player"].season} if game_state["current_player"] else None,
        "current_highest_bid": game_state["current_highest_bid"],
        "current_turn": game_state["current_turn"],
        "seconds_remaining": seconds_remaining,
        "team_a": {
            "name": team_a.name if team_a else None,
            "remaining_amount": remaining_money_a,
            "Players": [player.name for player in team_a.players]
        },
        "team_b": {
            "name": team_b.name if team_b else None,
            "remaining_amount": remaining_money_b,
            "Players": [player.name for player in team_b.players]
        }
    })


@app.route('/bid', methods=['POST'])
def bid():
    timeout_message = check_timeout()
    if timeout_message:
        return jsonify({"message": timeout_message, "timeout": True})

    data = request.get_json()
    team_name = data.get('team_name')
    bid_amount = data.get('bid_amount')

    if team_name == game_state["team_a"].name:
        team = game_state["team_a"]
        other_team_key = game_state["team_b"].name
    elif team_name == game_state["team_b"].name:
        team = game_state["team_b"]
        other_team_key = game_state["team_a"].name
    else:
        return jsonify({"error": "Invalid team name."}), 400

    if game_state["current_turn"] is not None and game_state["current_turn"] != team_name:
        return jsonify({"error": f"It's not {team_name}'s turn to bid."}), 400

    res = place_bid(team, game_state["current_highest_bid"], bid_amount)
    if res:
        game_state["current_highest_bid"] = bid_amount
        game_state["current_winning_team"] = team_name
        game_state["current_turn"] = other_team_key
        game_state["turn_started_at"] = time.time()
        game_state["no_of_passes"] = 0   # ADDED: a real bid resets the decline streak
        place_bid_response = f"{team_name} placed a bid of {bid_amount}."
    else:
        place_bid_response = f"{team_name} failed to place a bid of {bid_amount}."

    return jsonify({
        "message": place_bid_response,
        "current_highest_bid": game_state["current_highest_bid"],
        "current_winning_team": game_state["current_winning_team"]
    })


@app.route('/pass', methods=['POST'])
def pass_bid():
    timeout_message = check_timeout()
    if timeout_message:
        return jsonify({"message": timeout_message, "timeout": True})

    team_name = request.get_json().get('team_name')

    if team_name == game_state['team_a'].name:
        other_team_name = game_state["team_b"].name
    elif team_name == game_state['team_b'].name:
        other_team_name = game_state["team_a"].name
    else:
        return jsonify({"error": "Invalid team name."}), 400

    if game_state["current_turn"] is not None and game_state["current_turn"] != team_name:
        return jsonify({"error": f"It's not {team_name}'s turn to bid."}), 400

    # CASE 1: nobody has bid on this player yet
    if game_state["current_winning_team"] is None:
        if game_state["no_of_passes"] == 0:
            # first decline — give the other team a chance to bid
            game_state["no_of_passes"] = 1
            game_state["current_turn"] = other_team_name
            game_state["turn_started_at"] = time.time()
            return jsonify({
                "message": f"{team_name} passed. Waiting for {other_team_name} to respond.",
                "current_turn": game_state["current_turn"]
            })
        else:
            # second decline in a row — skip this player, send to end of queue
            skipped_player = game_state["current_player"]
            game_state["players"].append(skipped_player)  # goes to the back, not lost

            game_state["current_highest_bid"] = 0
            game_state["current_winning_team"] = None
            game_state["current_turn"] = None
            game_state["turn_started_at"] = None
            game_state["no_of_passes"] = 0

            game_state["current_player"] = game_state["players"].pop(0)
            next_player_info = {"name": game_state["current_player"].name, "season": game_state["current_player"].season}

            return jsonify({
                "message": f"Both teams passed on {skipped_player.name}. Moved to the end of the queue.",
                "next_player": next_player_info,
                "team_a_remaining_amount": game_state["team_a"].remaining_amount,
                "team_b_remaining_amount": game_state["team_b"].remaining_amount
            })

    # CASE 2: someone has already bid — normal sale to the current highest bidder
    else:
        winning_team_name = game_state["current_winning_team"]
        winning_team = game_state["team_a"] if winning_team_name == game_state["team_a"].name else game_state["team_b"]

        sold_player = game_state["current_player"]
        sold_price = game_state["current_highest_bid"]
        buy_player(sold_player, winning_team, sold_price)

        game_state["current_highest_bid"] = 0
        game_state["current_winning_team"] = None
        game_state["current_turn"] = None
        game_state["turn_started_at"] = None
        game_state["no_of_passes"] = 0

        if game_state["players"]:
            game_state["current_player"] = game_state["players"].pop(0)
            next_player_info = {"name": game_state["current_player"].name, "season": game_state["current_player"].season}
        else:
            game_state["current_player"] = None
            next_player_info = None

        return jsonify({
            "message": f"{team_name} passed. {winning_team.name} wins the bid for {sold_player.name} for {sold_price}.",
            "next_player": next_player_info,
            "team_a_remaining_amount": game_state["team_a"].remaining_amount,
            "team_b_remaining_amount": game_state["team_b"].remaining_amount
        })


if __name__ == '__main__':
    app.run(debug=True)