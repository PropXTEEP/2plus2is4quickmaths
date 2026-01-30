import streamlit as st
import random
import time

# --- SHARED STATE SETUP ---
@st.cache_resource
def get_global_state():
    return {
        "players": {}, 
        "history": [],
        "last_result": None,
        "is_spinning": False,
        "winning_color": "white"
    }

state = get_global_state()

# --- ROULETTE CONSTANTS ---
RED_NUMS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
ROULETTE_DATA = {
    i: "red" if i in RED_NUMS else "black" if i != 0 else "green" 
    for i in range(37)
}

# --- LOGIC FUNCTIONS ---
def resolve_bets(winning_number):
    win_color = ROULETTE_DATA[winning_number]
    for p_id, p_data in state["players"].items():
        if not p_data["bet"]: continue
        
        amt = p_data["bet"]["amount"]
        choice = p_data["bet"]["choice"]
        
        # Win Calculation
        is_win = False
        if choice == str(winning_number):
            p_data["balance"] += amt * 35
            is_win = True
        elif choice == win_color:
            p_data["balance"] += amt # Return bet + profit
            is_win = True
        else:
            p_data["balance"] -= amt

        # Handle Bankruptcy
        if p_data["balance"] <= 0:
            p_data["balance"] = 1000
            p_data["notif"] = "🏦 Bankrupt! The house gave you a $1,000 loan."
        elif is_win:
            p_data["notif"] = f"💰 You won with {choice}!"
        else:
            p_data["notif"] = f"💸 Lost ${amt} on {choice}."
            
        p_data["bet"] = None

# --- UI COMPONENTS ---
st.set_page_config(page_title="Streamlit Casino", layout="wide")
st.title("🎰 Live Multiplayer Roulette")

# Session Management
if "my_id" not in st.session_state:
    st.session_state.my_id = str(random.randint(1000, 9999))

# 1. SIDEBAR: Player Info
with st.sidebar:
    st.header("👤 Player Profile")
    if st.session_state.my_id not in state["players"]:
        name = st.text_input("Username")
        if st.button("Join Game"):
            state["players"][st.session_state.my_id] = {"name": name, "balance": 1000, "bet": None, "notif": ""}
    
    if st.session_state.my_id in state["players"]:
        p = state["players"][st.session_state.my_id]
        st.metric("Your Balance", f"${p['balance']:,}")
        if p["notif"]:
            st.info(p["notif"])
            p["notif"] = "" # Clear after showing

# 2. MAIN: The Visual Board
st.subheader("The Table")

def draw_board():
    # Creating a simple CSS-styled grid for the board
    rows = [
        [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
        [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
    ]
    
    # Render Zero
    st.markdown(f"<div style='background-color:green; color:white; text-align:center; border-radius:5px; padding:10px; margin-bottom:5px'>0 (Green)</div>", unsafe_allow_html=True)
    
    cols = st.columns(12)
    for r in range(3):
        for c in range(12):
            num = rows[r][c]
            color = "red" if num in RED_NUMS else "black"
            cols[c].markdown(f"<div style='background-color:{color}; color:white; text-align:center; border:1px solid white; border-radius:3
