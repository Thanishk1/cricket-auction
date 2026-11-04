# cricket-auction

A timed, two-team cricket player auction built with Flask. A Flask REST API keeps the game state on the server, and a browser UI polls it for updates.

> **Status: in progress.** The core game works. A pytest and Flask test-client suite is being added, and CI with GitHub Actions is planned.

## Features

- Two teams ("You" and "Bot") with a budget of 50 and 5 player slots each
- Players drawn at random from a pool, each with a role, a season, and a hidden skill rating
- Bidding with alternating turns, and a "Pass" option
- A 10-second turn timeout enforced on the server
- Browser UI that shows the current player, the highest bid, a countdown, and both teams' squads

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 and click **Start New Game**.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/start` | Start a new game and return the first player |
| GET | `/status` | Current player, highest bid, whose turn it is, seconds left, and both teams |
| POST | `/bid` | Place a bid. Body: `{"team_name": "You", "bid_amount": 3}` |
| POST | `/pass` | Pass on the current player. Body: `{"team_name": "You"}` |

## Design

- **Domain models:** `Player`, `Team`, and the `PlayerRole` enum are defined in `models.py` as Python dataclasses and an `Enum`, so squads, budgets, and slots are typed objects rather than loose dicts.
- **Separation of concerns:** bidding rules (`place_bid`, `buy_player`) live in `models.py`, and the HTTP layer and game state live in `app.py`.
- **Planned refactor:** move the module-level game state and the bid/pass/timeout logic into an `Auction` class, so the rules can be tested without going through HTTP.

## Project structure

```
.
├── app.py              # Flask app: routes, game state, timeout logic
├── models.py           # Player/Team dataclasses, bidding rules, player generation
├── templates/
│   └── index.html      # Browser UI
├── requirements.txt
└── README.md
```

## Known issues (to be covered by the test suite)

- If the first team passes and the other team never responds, the timeout can award the player at a price of 0.
- If only one player is left and both teams pass, that player is re-queued and comes straight back, so the auction cannot end.
- `buy_player` prints an error but does not signal failure, so a purchase that fails (no slots or not enough funds) is still reported as a sale.
- There is no end condition once both teams have filled their slots.
- `/bid` does not validate the request body, and `/status` fails if called before `/start`.
- The Bot team has no bidding logic yet, and the hidden skill rating is not used yet.

## Test automation plan (in progress)

None of the items below are done yet. They are checked off as each one is built and pushed. Each known issue above gets a failing test first, then a fix, so the commit history shows the bug, the test that catches it, and the repair.

**1. Unit tests (pytest): `models.py`**
- [ ] `place_bid`: rejects a bid at or below the current highest bid, rejects a bid above the team's remaining budget, accepts a valid bid
- [ ] `buy_player`: updates the squad, slots, and budget on success; refuses a purchase with no slots or not enough funds
- [ ] `generate_players`: returns the requested count with no duplicate names

**2. API tests (pytest and the Flask test client): `app.py`**
- [ ] `/start` resets all state and returns the first player
- [ ] `/bid`: valid bid, bid out of turn, invalid team name, bid above budget, malformed or missing body
- [ ] `/pass`: first pass, double pass, and pass after a bid (a normal sale)
- [ ] `/status` before `/start` and after the auction ends
- [ ] Turn timeout: a timeout after a real bid sells to the highest bidder, and a timeout with no bid never gives a player away for free (regression test for the known issue)
- [ ] Shared fixtures that reset game state and control the clock, so timeout tests run instantly
- [ ] Reusable test helpers: an `AuctionClient` class that wraps the Flask test client (start, bid, pass, status) and factory functions for teams and players, so tests stay short and readable

**3. UI tests (Playwright)**
- [ ] Start a game, place a bid, and check that the bid amount, turn label, and button states update
- [ ] The countdown appears and the buttons are disabled when it is not your turn
- [ ] A full auction reaches the "Auction Over" state

**4. Continuous integration (GitHub Actions)**
- [ ] A workflow that installs dependencies and runs the pytest suite on every push and pull request
- [ ] A step that runs the Playwright tests after the API tests pass
- [ ] A test report uploaded as a build artifact

**Other planned work**
- Bot bidding logic and scoring based on player skill
- An OpenAPI (Swagger) spec and a Postman collection for the API

## Tech

Python, Flask, HTML, JavaScript
