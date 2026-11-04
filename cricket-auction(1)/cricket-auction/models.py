from enum import Enum
from dataclasses import dataclass
import random

class PlayerRole(Enum):
    BATSMAN = "BATSMAN"
    BOWLER = "BOWLER"
    ALL_ROUNDER = "ALL_ROUNDER"
    WICKET_KEEPER="WICKET_KEEPER"

@dataclass
class Player:
    name:str
    role:PlayerRole
    season:int
    true_skill:int 
    is_decoy: bool = False


Names_By_Role = {
    PlayerRole.BATSMAN: ["Virat Kohli", "Steve Smith", "Joe Root", "Kane Williamson", "Babar Azam"],
    PlayerRole.BOWLER: ["Jasprit Bumrah", "Pat Cummins", "Trent Boult", "Rashid Khan", "Mitchell Starc"],
    PlayerRole.ALL_ROUNDER: ["Ben Stokes", "Shakib Al Hasan", "Hardik Pandya", "Ravindra Jadeja", "Andre Russell"],
    PlayerRole.WICKET_KEEPER: ["MS Dhoni", "Jos Buttler", "Quinton de Kock", "Rishabh Pant", "Kumar Sangakkara"]
}

def generate_player()-> Player:
    role = random.choice(list(PlayerRole))
    name = random.choice(Names_By_Role[role])
    season = random.randint(2016, 2026)
    is_decoy = random.random()<0.2
    if is_decoy:
        true_skill = random.randint(10, 40)   # big name, weak actual skill
    else:
        true_skill = random.randint(40, 100)

    return Player(name=name, role=role, season=season,true_skill=true_skill, is_decoy=is_decoy)

def generate_players(count: int) -> list[Player]:
    players = []
    used_names = set()

    while len(players) < count:
        player = generate_player()
        if player.name not in used_names:
            used_names.add(player.name)
            players.append(player)

    return players
@dataclass 
class Team:
    name:str
    players:list[Player]
    slots_to_fill:int
    total_amount:int
    remaining_amount:int

def buy_player(player:Player,team:Team,bidding_amount:int):
    if team.slots_to_fill<=0:
        print("Cannot buy player, no slots available")
    elif bidding_amount>team.remaining_amount:
        print("Cannot buy player, not enough funds")
    else:
        team.players.append(player)
        team.slots_to_fill-=1
        team.remaining_amount-=bidding_amount
        print(f"{team.name} successfully bought {player.name} for {bidding_amount}. Remaining amount: {team.remaining_amount}")

def place_bid(bidder: Team, current_highest_bid: int, new_bid: int) -> bool:
    if new_bid <= current_highest_bid:
        print(f"Bid must be higher than current highest bid of {current_highest_bid}")
        return False
    if new_bid > bidder.remaining_amount:
        print(f"{bidder.name} cannot afford {new_bid}, only has {bidder.remaining_amount}")
        return False
    return True

def conduct_auction_round(player: Player, team_a: Team, team_b: Team, bid_sequence: list[tuple[Team, int]]):
    current_highest_bid = 0
    highest_bidder = None
    out_teams = []  # teams that have passed or made an invalid bid

    for team, bid in bid_sequence:
        if team in out_teams:
            continue  

        if bid == 0:
            print(f"{team.name} passes.")
            out_teams.append(team)
            continue

        if place_bid(team, current_highest_bid, bid):
            current_highest_bid = bid
            highest_bidder = team
        else:
            # invalid bid (too low or can't afford) counts as being out
            out_teams.append(team)

        # if both teams are out, no point continuing
        if len(out_teams) == 2:
            break

    if highest_bidder:
        buy_player(player, highest_bidder, current_highest_bid)
    else:
        print(f"No bids placed for {player.name}. Player remains unsold.")

def random_bid_sequence(team_a: Team, team_b: Team) -> list[tuple[Team, int]]:
    sequence = []
    current_bid = 0
    teams = [team_a, team_b]

    for _ in range(6):  # up to 6 rounds of back-and-forth
        team = teams[_ % 2]  # alternate turns: team_a, team_b, team_a, ...
        if random.random() < 0.3:  # 30% chance this team passes
            sequence.append((team, 0))
            break
        current_bid += random.randint(1, 5)
        if current_bid > team.remaining_amount:
            sequence.append((team, 0))  # can't afford, forced pass
            break
        sequence.append((team, current_bid))

    return sequence


def run_simulation():
    """Standalone console simulation of an auction (not used by the Flask app)."""
    generated_players = generate_players(10)
    team_a = Team(name="Team A", players=[], slots_to_fill=11, total_amount=100, remaining_amount=100)
    team_b = Team(name="Team B", players=[], slots_to_fill=11, total_amount=100, remaining_amount=100)

    for player in generated_players:
        sequence = random_bid_sequence(team_a, team_b)
        conduct_auction_round(player, team_a, team_b, sequence)

    print("\n--- Final Results ---")
    print(team_a)
    print(team_b)


if __name__ == "__main__":
    run_simulation()