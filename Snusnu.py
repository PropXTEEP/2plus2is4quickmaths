import streamlit as st
import random
import time
from datetime import datetime

# --- SHARED STATE SETUP ---
@st.cache_resource
def get_global_state():
    return {
        "players": {}, 
        "history": [],
        "last_result": None,
        "winning_color": "white",
        "last_spin_time": time.time()
    }

state = get_global_state()

# --- ROULETTE CONSTANTS ---
RED_NUMS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
ROULETTE_DATA = {
    i: "red" if i in RED_NUMS else "black" if i != 0 else "green" 
    for i in range(37)
}

def resolve_bets(winning_number):
    win_color = ROULETTE_DATA[winning_number]
    for p_id, p_data in state["players"].items():
        if not p_data["bet"]: continue
        
        amt = p_data["bet"]["amount"]
        choice = p_data["bet"]["choice"]
        
        is_win = False
        if choice == str(winning_number):
            p_data["balance"] += amt * 35
            is_win = True
        elif choice == win_color:
            p_data["balance"] += amt 
            is_win = True
        else:
            p_data["balance"] -= amt

        if p_data["balance"] <= 0:
            p_data["balance"] = 1000
            p_data["notif"] = "🚨 BANKRUPT! House reset you to $1,000."
        elif is_win:
            p_data["notif"] = f"💰 WINNER! +${amt if choice != str(winning_number) else amt*35}"
        else:
            p_data["notif"] = f"💸 LOST ${amt}."
            
        p_data["bet"] = None

# --- UI SETUP ---
st.set_page_config(page_title="Live Roulette", layout="wide")

# Player ID session sync
if "my_id" not in st.session_state:
    st.session_state.my_id = str(random.randint(1000, 9999))

# 1. THE CLOCK (Automatic Spinning)
SPIN_INTERVAL = 60 # seconds
seconds_since_last = time.time() - state["last_spin_time"]
seconds_left = int(SPIN_INTERVAL - seconds_since_last)

if seconds_left <= 0:
    # Trigger Auto-Spin
    res = random.randint(0, 36)
    state["last_result"] = res
    state["winning_color"] = ROULETTE_DATA[res]
    state["history"].insert(0, f"{res} ({state['winning_color']})")
    resolve_bets(res)
    state["last_spin_time"] = time.time()
    st.rerun()

# 2. HEADER & SIDEBAR
st.title("🎰 Live Multiplayer Roulette")
with st.sidebar:
    st.header("👤 Your Wallet")
    if st.session_state.my_id not in state["players"]:
        name = st.text_input("Enter Nickname")
        if st.button("Join Table"):
            state["players"][st.session_state.my_id] = {"name": name, "balance": 1000, "bet": None, "notif": ""}
    
    if st.session_state.my_id in state["players"]:
        p = state["players"][st.session_state.my_id]
        st.metric("Balance", f"${p['balance']:,}")
        if p["notif"]:
            st.toast(p["notif"])
            p["notif"] = ""

# 3. VISUAL BOARD (Fixed Syntax)
st.subheader(f"Next Spin in: {seconds_left}s")

def draw_board():
    rows = [
        [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
        [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
        [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
    ]
    st.markdown("<div style='background-color:green; color:white; text-align:center; border-radius:5px; padding:10px; margin-bottom:10px;'>0</div>", unsafe_allow_html=True)
    cols = st.columns(12)
    for r in range(3):
        for c in range(12):
            num = rows[r][c]
            color = "red" if num in RED_NUMS else "black"
            # FIXED MULTILINE STRING BELOW
            style = f"background-color:{color}; color:white; text-align:center; border:1px solid white; border-radius:3px; padding:5px; margin-bottom:2px;"
            cols[c].markdown(f"<div style='{style}'>{num}</div>", unsafe_allow_html=True)

draw_board()

# 4. BETTING AREA
if st.session_state.my_id in state["players"]:
    p = state["players"][st.session_state.my_id]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        amt = st.number_input("Amount", 10, p["balance"], step=50)
    with c2:
        choice = st.selectbox("Position", ["red", "black"] + [str(i) for i in range(37)])
    with c3:
        st.write("###")
        if st.button("Place Bet", use_container_width=True):
            state["players"][st.session_state.my_id]["bet"] = {"amount": amt, "choice": choice}

# 5. LIVE FEEDS
st.divider()
col_a, col_b = st.columns(2)
with col_a:
    st.write("### 👥 Active Bets")
    for pid, pdata in state["players"].items():
        status = f"✅ ${pdata['bet']['amount']} on {pdata['bet']['choice']}" if pdata["bet"] else "⏳ Waiting..."
        st.write(f"**{pdata['name']}**: {status}")

with col_b:
    if state["last_result"] is not None:
        st.markdown(f"""
            <div style="text-align:center; padding:10px; border: 4px solid gold; border-radius:10px;">
                <p>LAST RESULT</p>
                <h1 style="color:{state['winning_color']};">{state['last_result']}</h1>
            </div>
        """, unsafe_allow_html=True)
    st.write(f"**History:** {', '.join(state['history'][:8])}")

# 6. AUTO-REFRESH (Keep players synced)
time.sleep(2)
st.rerun()
