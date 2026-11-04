# Cricket Auction

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

## Planned

- pytest and Flask test-client tests for bidding, passing, and timeouts
- A GitHub Actions workflow that runs the tests on every push
- Browser tests for the auction UI
- Bot bidding logic and scoring based on player skill

## Tech

Python, Flask, HTML, JavaScript
