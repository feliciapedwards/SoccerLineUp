# Soccer LineUp

A simple Streamlit app for planning soccer player rotations and generating balanced lineups by quarter/half intervals.

## Features

- Define a dynamic roster of players
- Set the number of players on the field, half duration, substitution interval, and number of halves
- Specify which positions each player is eligible to play
- Generate balanced lineups across time blocks
- View schedule, total playing time, and position assignment counts

## Requirements

- Python 3.10+
- `streamlit`
- `pandas`

## Setup

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd SoccerLineUp
   ```

2. Install dependencies:

   ```bash
   python -m pip install streamlit pandas
   ```

## Run

```bash
streamlit run rotation.py
```

Then open the local URL displayed in the terminal.

## Usage

1. Enter players in the editable table.
2. Configure the game settings in the sidebar:
   - Players on field
   - Half length
   - Substitution interval
   - Number of halves
3. Click `Generate Lineups`.
4. Review the generated rotation schedule, playing time totals, and position counts.

## Notes

- The app currently uses a simple rotation algorithm to fairly distribute minutes and position assignments.
- If a player is not eligible for a position, the app will display `No eligible player` for that slot.

## File

- `rotation.py` — main Streamlit application

## License

This repository does not include a license file. Add one if you want to define reuse terms.
