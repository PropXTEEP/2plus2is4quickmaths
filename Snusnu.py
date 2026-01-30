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
        "winning_color": "white",
        "last_spin_time": time.time()
    }

state = get_global_state()

# --- ROULETTE CONSTANTS & LOGIC ---
RED_NUMS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
ROULETTE_DATA = {i: "red" if i in RED_NUMS else "black" if i != 0 else "green" for i in range(37)}

def resolve_bets(winning_number):
    win_color = ROULETTE_DATA[winning_number]
    for p_id, p_data in state["players"].items():
        if not p_data["bet"]: continue
        
        amt = p_data["bet"]["amount"]
        choice = p_data["bet"]["choice"]
        win = False
        multiplier = 0
        
        # Payout Logic
        if choice == str(winning_number): # Single Number
            multiplier = 35
            win = True
        elif choice == win_color: # Red/Black
            multiplier = 1
            win = True
        elif choice == "even" and winning_number != 0 and winning_number % 2 == 0:
            multiplier = 1
            win = True
        elif choice == "odd" and winning_number % 2 != 0:
            multiplier = 1
            win = True
        elif choice == "1st 12" and 1 <= winning_number <= 12:
            multiplier = 2
            win = True
        elif choice == "2nd 12" and 13 <= winning_number <= 24:
            multiplier = 2
            win = True
        elif choice == "3rd 12" and 25 <= winning_number <= 36:
            multiplier = 2
            win = True
        
        if win:
            p_data["balance"] += (amt * multiplier)
            p_data["notif"] = f"💰 +${amt * multiplier} (Hit {choice}!)"
        else:
            p_data["balance"] -= amt
            p_data["notif"] = f"💸 -${amt} (Lost on {choice})"

        # Bankruptcy Check
        if p_data["balance"] <= 0:
            p_data["balance"] = 1000
            p_data["notif"] = "🚨 BANKRUPT! You've been reset to $1,000."
            
        p_data["bet"] = None

# --- UI SETUP ---
st.set_page_config(page_title="Fast Roulette", layout="wide")

if "my_id" not in st.session_state:
    st.session_state.my_id = str(random.randint(1000, 9999))

# 1. THE 20-SECOND CLOCK
SPIN_INTERVAL = 20 
seconds_left = int(SPIN_INTERVAL - (time.time() - state["last_spin_time"]))

if seconds_left <= 0:
    res = random.randint(0, 36)
    state["last_result"] = res
    state["winning_color"] = ROULETTE_DATA[res]
    state["history"].insert(0, f"{res} {state['winning_color']}")
    resolve_bets(res)
    state["last_spin_time"] = time.time()
    st.rerun()

# 2. SIDEBAR (WALLET & PAYOUTS)
with st.sidebar:
    st.title("🪙 Casino Floor")
    if st.session_state.my_id not in state["players"]:
        name = st.text_input("Name")
        if st.button("Sit at Table"):
            state["players"][st.session_state.my_id] = {"name": name, "balance": 1000, "bet": None, "notif": ""}
    
    if st.session_state.my_id in state["players"]:
        p = state["players"][st.session_state.my_id]
        st.metric("Your Cash", f"${p['balance']:,}")
        if p["notif"]:
            st.toast(p["notif"])
            p["notif"] = ""
            
    st.divider()
    st.write("### 📜 Payout Table")
    st.table({
        "Bet Type": ["Single #", "Dozens", "Red/Black", "Even/Odd"],
        "Payout": ["35:1", "2:1", "1:1", "1:1"]
    })

# 3. MAIN INTERFACE
c1, c2 = st.columns([2, 1])
with c1:
    st.subheader(f"Next Spin in: {seconds_left}s")
with c2:
    if state["last_result"] is not None:
        color_hex = "#FF4B4B" if state["winning_color"] == "red" else "#31333F"
        if state["winning_color"] == "green": color_hex = "#29B09D"
        st.markdown(f"**LAST BALL:** <span style='font-size: 24px; padding: 5px 15px; border-radius: 10px; background-color: {color_hex}; color: white;'>{state['last_result']}</span>", unsafe_allow_html=True)

# Visual Table
def draw_table():
    rows = [[3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]]
    st.markdown("<div style='background-color:#29B09D; color:white; text-align:center; border-radius:5px; padding:5px; margin-bottom:5px;'>0</div>", unsafe_allow_html=True)
    cols = st.columns(12)
    for r in range(3):
        for idx, c_ui in enumerate(cols):
            num = rows[r][idx]
            color = "#FF4B4B" if num in RED_NUMS else "#31333F"
            c_ui.markdown(f"<div style='background-color:{color}; color:white; text-align:center; border:1px solid #555; border-radius:3px; font-size:12px;'>{num}</div>", unsafe_allow_html=True)

draw_table()

# 4. BETTING PANEL
if st.session_state.my_id in state["players"]:
    p = state["players"][st.session_state.my_id]
    with st.container(border=True):
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            amt = st.number_input("Wager ($)", 10, p["balance"], step=50)
        with bc2:
            options = ["red", "black", "even", "odd", "1st 12", "2nd 12", "3rd 12"] + [str(i) for i in range(37)]
            choice = st.selectbox("Spot", options)
        with bc3:
            st.write("###")
            if st.button("PLACE BET", use_container_width=True, type="primary"):
                state["players"][st.session_state.my_id]["bet"] = {"amount": amt, "choice": choice}
                st.success("Bet Locked!")

# 5. LIVE LOBBY
st.divider()
st.write("### 👥 Table Players")
player_cols = st.columns(4)
for i, (pid, pdata) in enumerate(state["players"].items()):
    with player_cols[i % 4]:
        bet_info = f"💰 {pdata['bet']['choice']} (${pdata['bet']['amount']})" if pdata["bet"] else "Watching..."
        st.info(f"**{pdata['name']}**\n\n{bet_info}")

# Auto-refresh
time.sleep(1)
st.rerun()
