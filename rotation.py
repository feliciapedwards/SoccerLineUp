import streamlit as st
import pandas as pd
from itertools import cycle

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

st.sidebar.header("Game Settings")
players_on_field = st.sidebar.number_input("Players on field", value=7, min_value=1)
half_length = st.sidebar.number_input("Half length (minutes)", value=25)
sub_interval = st.sidebar.number_input("Sub every X minutes", value=7)
halves = st.sidebar.number_input("Number of halves", value=2)

st.header("1. Enter Players")

default_players = pd.DataFrame({
    "Player": ["Player 1", "Player 2", "Player 3", "Player 4", "Player 5", "Player 6", "Player 7", "Player 8", "Player 9"],
    **{pos: True for pos in POSITIONS}
})

players_df = st.data_editor(
    default_players,
    num_rows="dynamic",
    use_container_width=True
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

def generate_lineups(players_df):
    players = players_df["Player"].dropna().tolist()
    play_minutes = {p: 0 for p in players}
    position_counts = {p: {pos: 0 for pos in POSITIONS} for p in players}
    last_sat = {p: -999 for p in players}

    blocks = make_time_blocks(half_length, sub_interval, halves)
    schedule = []

    for block_index, block in enumerate(blocks):
        lineup = {}

        available_players = players.copy()

        for pos in POSITIONS:
            eligible = [
                p for p in available_players
                if bool(players_df.loc[players_df["Player"] == p, pos].iloc[0])
            ]

            if not eligible:
                lineup[pos] = "No eligible player"
                continue

            chosen = sorted(
                eligible,
                key=lambda p: (
                    play_minutes[p],
                    position_counts[p][pos],
                    -last_sat[p]
                )
            )[0]

            lineup[pos] = chosen
            available_players.remove(chosen)
            position_counts[chosen][pos] += 1

        playing = set(lineup.values())
        for p in players:
            if p in playing:
                play_minutes[p] += block["Duration"]
            else:
                last_sat[p] = block_index

        row = {
            "Half": block["Half"],
            "Time": f"{block['Start']}-{block['End']} min",
            **lineup
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