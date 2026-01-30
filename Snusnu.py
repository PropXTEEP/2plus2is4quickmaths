import streamlit as st
import random
import time

# --- SHARED STATE SETUP ---
@st.cache_resource
def get_global_state():
    return {
        "players": {}, # {id: {name, balance, bet, notif}}
        "history": [],
        "last_result": None,
        "winning_color": "white",
        "last_spin_time": time.time()
    }

state = get_global_state()

# --- ROULETTE CONSTANTS ---
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
        
        # Logic for Payouts
        if choice == str(winning_number): 
            multiplier = 35
            win = True
        elif choice == win_color: 
            multiplier = 1
            win = True
        elif choice == "even" and winning_number != 0 and winning_number % 2 == 0:
            multiplier = 1
            win = True
        elif choice == "odd" and winning_number % 2 != 0:
            multiplier = 1
            win = True
        elif choice in ["1st 12", "2nd 12", "3rd 12"]:
            low, high = {"1st 12": (1,12), "2nd 12": (13,24), "3rd 12": (25,36)}[choice]
            if low <= winning_number <= high:
                multiplier = 2
                win = True
        
        if win:
            p_data["balance"] += (amt * multiplier)
            p_data["notif"] = f"🎉 WIN! +${amt * multiplier}"
        else:
            p_data["balance"] -= amt
            p_data["notif"] = f"💸 LOST ${amt}"

        # Bankruptcy Check
        if p_data["balance"] <= 0:
            p_data["balance"] = 1000
            p_data["notif"] = "🏦 Reset! Back to $1,000."
            
        p_data["bet"] = None

# --- UI SETUP ---
st.set_page_config(page_title="Multiplayer Roulette", layout="wide")

if "my_id" not in st.session_state:
    st.session_state.my_id = str(random.randint(1000, 9999))

# 1. THE 30-SECOND GLOBAL TIMER
SPIN_INTERVAL = 30 
elapsed = time.time() - state["last_spin_time"]
seconds_left = max(0, int(SPIN_INTERVAL - elapsed))

if seconds_left <= 0:
    res = random.randint(0, 36)
    state["last_result"] = res
    state["winning_color"] = ROULETTE_DATA[res]
    state["history"].insert(0, f"{res} {state['winning_color']}")
    resolve_bets(res)
    state["last_spin_time"] = time.time()
    st.rerun()

# 2. HEADER & LAST RESULT
t1, t2 = st.columns([3, 1])
with t1:
    st.title("🎰 Live 30s Roulette")
    st.subheader(f"Next Spin in: `{seconds_left}s`")
with t2:
    if state["last_result"] is not None:
        c_hex = {"red": "#FF4B4B", "black": "#31333F", "green": "#29B09D"}[state["winning_color"]]
        st.markdown(f"""
            <div style="background-color:{c_hex}; border-radius:15px; padding:20px; text-align:center; color:white; border: 2px solid #gold;">
                <small>LAST RESULT</small><br><b style="font-size:40px;">{state['last_result']}</b>
            </div>
        """, unsafe_allow_html=True)

# 3. SIDEBAR: WALLET
with st.sidebar:
    st.header("👤 Your Seat")
    if st.session_state.my_id not in state["players"]:
        name = st.text_input("Username", placeholder="Enter name to play...")
        if st.button("Join Game", use_container_width=True):
            state["players"][st.session_state.my_id] = {"name": name, "balance": 1000, "bet": None, "notif": ""}
    
    if st.session_state.my_id in state["players"]:
        p = state["players"][st.session_state.my_id]
        st.metric("Your Balance", f"${p['balance']:,}")
        if p["notif"]:
            st.toast(p["notif"])
            p["notif"] = ""
    
    st.divider()
    st.write("### 🕒 History")
    st.write(", ".join(state["history"][:10]))

# 4. BETTING TABLE (VISUAL)
def draw_table():
    rows = [[3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]]
    st.markdown("<div style='background-color:#29B09D; color:white; text-align:center; border-radius:5px; padding:5px; margin-bottom:5px;'>0</div>", unsafe_allow_html=True)
    cols = st.columns(12)
    for r in range(3):
        for idx, col_ui in enumerate(cols):
            num = rows[r][idx]
            color = "#FF4B4B" if num in RED_NUMS else "#31333F"
            col_ui.markdown(f"<div style='background-color:{color}; color:white; text-align:center; border:1px solid #555; border-radius:3px; font-size:14px;'>{num}</div>", unsafe_allow_html=True)

draw_table()

# 5. ACTION AREA
if st.session_state.my_id in state["players"]:
    p = state["players"][st.session_state.my_id]
    with st.container(border=True):
        bc1, bc2, bc3 = st.columns([1, 1, 1])
        with bc1:
            amt = st.number_input("Wager", 10, p["balance"], step=50)
        with bc2:
            options = ["red", "black", "even", "odd", "1st 12", "2nd 12", "3rd 12"] + [str(i) for i in range(37)]
            choice = st.selectbox("Position", options)
        with bc3:
            st.write("###")
            if st.button("CONFIRM BET", use_container_width=True, type="primary"):
                state["players"][st.session_state.my_id]["bet"] = {"amount": amt, "choice": choice}
                st.success(f"Bet set on {choice}!")

# 6. LIVE MULTIPLAYER LOBBY
st.divider()
st.subheader("👥 Players at Table")
# Show everyone's balance and their current move
lobby_cols = st.columns(4)
for i, (pid, pdata) in enumerate(state["players"].items()):
    with lobby_cols[i % 4]:
        bet_label = f"**Bet:** {pdata['bet']['choice']} (${pdata['bet']['amount']})" if pdata["bet"] else "*Waiting...*"
        st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 10px; background-color: #f9f9f9;">
                <h4 style="margin:0;">{pdata['name']}</h4>
                <p style="margin:0; color: green;">💰 ${pdata['balance']:,}</p>
                <hr style="margin:5px 0;">
                <small>{bet_label}</small>
            </div>
        """, unsafe_allow_html=True)

# Refresh to sync with other players and the timer
time.sleep(1)
st.rerun()
