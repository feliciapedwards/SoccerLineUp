import streamlit as st
import pandas as pd

st.set_page_config(page_title="Soccer Rotation Planner", layout="wide")

st.title("⚽ Soccer Rotation Planner")

POSITIONS = [
    "Keeper",
    "Left Defender",
    "Right Defender",
    "Left Midfield",
    "Center Midfield",
    "Right Midfield",
    "Forward",
]
FEMALE_COLUMN = "Female"
MIN_FEMALES_ON_FIELD = 2

st.sidebar.header("Game Settings")
players_on_field = st.sidebar.number_input(
    "Players on field",
    value=7,
    min_value=1,
    max_value=len(POSITIONS),
)
half_length = st.sidebar.number_input("Half length (minutes)", value=25)
sub_interval = st.sidebar.number_input("Sub every X minutes", value=7)
halves = st.sidebar.number_input("Number of halves", value=2)
st.sidebar.info("The rotation requires at least 2 female players on the field at all times.")

st.header("1. Enter Players")

default_players = pd.DataFrame({
    "Player": [
        "Player 1",
        "Player 2",
        "Player 3",
        "Player 4",
        "Player 5",
        "Player 6",
        "Player 7",
        "Player 8",
        "Player 9",
    ],
    FEMALE_COLUMN: [True, True, False, False, False, False, False, False, False],
    **{pos: True for pos in POSITIONS},
})

players_df = st.data_editor(
    default_players,
    num_rows="dynamic",
    use_container_width=True,
)

def make_time_blocks(half_length, sub_interval, halves):
    blocks = []
    for half in range(1, halves + 1):
        start = 0
        while start < half_length:
            end = min(start + sub_interval, half_length)
            blocks.append({
                "Half": half,
                "Start": start,
                "End": end,
                "Duration": end - start
            })
            start = end
    return blocks

def player_cost(player, pos, play_minutes, position_counts, last_sat):
    return (
        play_minutes[player],
        position_counts[player][pos],
        -last_sat[player],
        player,
    )


def choose_lineup(player_data, players, positions, play_minutes, position_counts, last_sat):
    female_players = [p for p in players if player_data.at[p, FEMALE_COLUMN]]
    if len(female_players) < MIN_FEMALES_ON_FIELD:
        return None, f"Roster must contain at least {MIN_FEMALES_ON_FIELD} female players."

    eligible_by_position = {
        pos: [p for p in players if player_data.at[p, pos]]
        for pos in positions
    }
    for pos, eligible in eligible_by_position.items():
        if not eligible:
            return None, f"No eligible player for position {pos}."

    positions_order = sorted(positions, key=lambda pos: len(eligible_by_position[pos]))
    best_lineup = None
    best_score = None

    def remaining_female_capacity(used_players, remaining_positions):
        remaining_females = {
            p
            for p in female_players
            if p not in used_players
            and any(player_data.at[p, pos] for pos in remaining_positions)
        }
        return min(len(remaining_females), len(remaining_positions))

    def search(index, current_lineup, used_players, female_count, score_list):
        nonlocal best_lineup, best_score
        if index == len(positions_order):
            if female_count < MIN_FEMALES_ON_FIELD:
                return
            current_score = tuple(score_list)
            if best_score is None or current_score < best_score:
                best_score = current_score
                best_lineup = current_lineup.copy()
            return

        pos = positions_order[index]
        remaining_positions = positions_order[index + 1 :]
        candidates = sorted(
            [p for p in eligible_by_position[pos] if p not in used_players],
            key=lambda p: player_cost(p, pos, play_minutes, position_counts, last_sat),
        )

        for p in candidates:
            next_female_count = female_count + (1 if player_data.at[p, FEMALE_COLUMN] else 0)
            max_additional_females = remaining_female_capacity(used_players | {p}, remaining_positions)
            if next_female_count + max_additional_females < MIN_FEMALES_ON_FIELD:
                continue

            current_lineup[pos] = p
            used_players.add(p)
            score_list.append(player_cost(p, pos, play_minutes, position_counts, last_sat))

            search(index + 1, current_lineup, used_players, next_female_count, score_list)

            score_list.pop()
            used_players.remove(p)
            del current_lineup[pos]

    search(0, {}, set(), 0, [])

    if best_lineup is None:
        return None, "Unable to build a valid lineup with the current roster and constraints."
    return best_lineup, None


def generate_lineups(players_df):
    players = players_df["Player"].dropna().tolist()
    if len(players) < players_on_field:
        raise ValueError("Not enough players entered to fill the requested number of field positions.")

    player_data = players_df.set_index("Player")
    play_minutes = {p: 0 for p in players}
    position_counts = {p: {pos: 0 for pos in POSITIONS} for p in players}
    last_sat = {p: -999 for p in players}

    selected_positions = POSITIONS[:players_on_field]
    blocks = make_time_blocks(half_length, sub_interval, halves)
    schedule = []

    for block_index, block in enumerate(blocks):
        lineup, error = choose_lineup(
            player_data,
            players,
            selected_positions,
            play_minutes,
            position_counts,
            last_sat,
        )
        if error:
            raise ValueError(error)

        for pos in selected_positions:
            player = lineup[pos]
            position_counts[player][pos] += 1

        playing = set(lineup.values())
        for p in players:
            if p in playing:
                play_minutes[p] += block["Duration"]
            else:
                last_sat[p] = block_index

        row = {
            "Half": block["Half"],
            "Time": f"{block['Start']}-{block['End']} min",
            **lineup,
        }
        schedule.append(row)

    return pd.DataFrame(schedule), play_minutes, position_counts

st.header("2. Generate Rotation")

if st.button("Generate Lineups"):
    schedule_df, play_minutes, position_counts = generate_lineups(players_df)

    st.subheader("Rotation Schedule")
    st.dataframe(schedule_df, use_container_width=True)

    st.subheader("Playing Time")
    minutes_df = pd.DataFrame({
        "Player": list(play_minutes.keys()),
        "Total Minutes": list(play_minutes.values())
    }).sort_values("Total Minutes", ascending=False)

    st.dataframe(minutes_df, use_container_width=True)

    st.subheader("Position Counts")
    pos_df = pd.DataFrame(position_counts).T.reset_index()
    pos_df = pos_df.rename(columns={"index": "Player"})
    st.dataframe(pos_df, use_container_width=True)