import streamlit as st
import random
import time

# --- SHARED STATE SETUP ---
@st.cache_resource
def get_global_state():
    return {
        "players": {}, 
        "history": [], 
        "chat": [],
        "last_result": None,
        "winning_color": "white",
        "last_spin_time": time.time()
    }

state = get_global_state()

# --- ROULETTE CONSTANTS ---
RED_NUMS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

def get_color(n):
    if n == 0: return "green"
    return "red" if n in RED_NUMS else "black"

def resolve_bets(winning_number):
    win_color = get_color(winning_number)
    # Dealer announcement
    state["chat"].insert(0, f"🎙️ **Dealer**: Number {winning_number} {win_color.upper()}!")
    
    for p_id, p_data in state["players"].items():
        if not p_data["bet"]: continue
        
        amt = p_data["bet"]["amount"]
        choice = p_data["bet"]["choice"]
        win = False
        mult = 0
        
        # FIXED INDENTATION LOGIC
        if choice == str(winning_number):
            mult, win = 35, True
        elif choice == win_color:
            mult, win = 1, True
        elif choice == "even" and winning_number != 0 and winning_number % 2 == 0:
            mult, win = 1, True
        elif choice == "odd" and winning_number % 2 != 0:
            mult, win = 1, True
        elif choice in ["1st 12", "2nd 12", "3rd 12"]:
            bounds = {"1st 12": (1,12), "2nd 12": (13,24), "3rd 12": (25,36)}[choice]
            if bounds[0] <= winning_number <= bounds[1]:
                mult, win = 2, True
        
        if win:
            p_data["balance"] += (amt * mult)
            p_data["notif"] = f"🔥 WIN! +${amt * mult}"
        else:
            p_data["balance"] -= amt
            p_data["notif"] = f"💸 LOST ${amt}"

        if p_data["balance"] <= 0:
            p_data["balance"] = 1000
            p_data["notif"] = "🏦 RESET! House gave you $1,000."
            
        p_data["bet"] = None

# --- UI SETUP ---
st.set_page_config(page_title="Live Multiplayer Roulette", layout="wide")

if "my_id" not in st.session_state:
    st.session_state.my_id = str(random.randint(1000, 9999))

# 1. GLOBAL TIMER (30s)
SPIN_INTERVAL = 30 
elapsed = time.time() - state["last_spin_time"]
seconds_left = max(0, int(SPIN_INTERVAL - elapsed))

if seconds_left <= 0:
    res = random.randint(0, 36)
    state["last_result"] = res
    state["winning_color"] = get_color(res)
    state["history"].insert(0, res)
    resolve_bets(res)
    state["last_spin_time"] = time.time()
    st.rerun()

# 2. TOP BAR: HISTORY
h_cols = st.columns(13)
h_cols[0].write("**History:**")
for i, num in enumerate(state["history"][:12]):
    c = "#FF4B4B" if get_color(num) == "red" else "#31333F" if get_color(num) == "black" else "#29B09D"
    h_cols[i+1].markdown(f'<div style="background:{c}; color:white; border-radius:50%; width:28px; height:28px; text-align:center; font-size:12px; line-height:28px; font-weight:bold; border:1px solid white;">{num}</div>', unsafe_allow_html=True)

# 3. HEADER
t1, t2 = st.columns([3, 1])
with t1:
    st.title("🎰 Live Multiplayer Roulette")
    st.subheader(f"Next Spin in: `{seconds_left}s`")
with t2:
    if state["last_result"] is not None:
        c_hex = {"red": "#FF4B4B", "black": "#31333F", "green": "#29B09D"}[state["winning_color"]]
        st.markdown(f'<div style="background-color:{c_hex}; border-radius:10px; padding:15px; text-align:center; color:white; border: 3px solid gold;"><small>RESULT</small><br><b style="font-size:35px;">{state["last_result"]}</b></div>', unsafe_allow_html=True)

# 4. SIDEBAR & CHAT
with st.sidebar:
    st.header("👤 Player Profile")
    if st.session_state.my_id not in state["players"]:
        name = st.text_input("Choose Nickname")
        if st.button("Join Table", use_container_width=True):
            state["players"][st.session_state.my_id] = {"name": name, "balance": 1000, "bet": None, "notif": ""}
    
    if st.session_state.my_id in state["players"]:
        p = state["players"][st.session_state.my_id]
        st.metric("Your Balance", f"${p['balance']:,}")
        if p["notif"]:
            st.toast(p["notif"])
            p["notif"] = ""
        
        st.divider()
        st.write("### 💬 Live Chat")
        with st.form("chat_form", clear_on_submit=True):
            msg = st.text_input("Say something...")
            if st.form_submit_button("Send") and msg:
                state["chat"].insert(0, f"**{p['name']}**: {msg}")
                st.rerun()
        for m in state["chat"][:10]:
            st.markdown(m)

# 5. BOARD
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
            col_ui.markdown(f"<div style='background-color:{color}; color:white; text-align:center; border:1px solid #555; border-radius:3px; font-size:12px;'>{num}</div>", unsafe_allow_html=True)
draw_table()

# 6. BETTING
if st.session_state.my_id in state["players"]:
    p = state["players"][st.session_state.my_id]
    
    # Session state for input persistence
    if "current_wager" not in st.session_state:
        st.session_state.current_wager = 10

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 2, 2])
        with c1:
            amt = st.number_input("Wager", 10, p["balance"], value=st.session_state.current_wager, step=50)
        with c2:
            st.write("###")
            if st.button("🚨 ALL IN"):
                st.session_state.current_wager = p["balance"]
                st.rerun()
        with c3:
            choice = st.selectbox("Position", ["red", "black", "even", "odd", "1st 12", "2nd 12", "3rd 12"] + [str(i) for i in range(37)])
        with c4:
            st.write("###")
            if st.button("CONFIRM BET", type="primary", use_container_width=True):
                state["players"][st.session_state.my_id]["bet"] = {"amount": amt, "choice": choice}
                st.session_state.current_wager = 10
                st.success("Bet Locked!")

# 7. LOBBY
st.divider()
st.subheader("👥 Live Players")
lcols = st.columns(4)
for i, (pid, pdata) in enumerate(state["players"].items()):
    with lcols[i % 4]:
        bet_info = f"🔥 ALL IN {pdata['bet']['choice']}!" if pdata["bet"] and pdata["bet"]["amount"] >= pdata["balance"] else (f"Bet: {pdata['bet']['choice']}" if pdata["bet"] else "Watching...")
        st.markdown(f'<div style="border:1px solid #ddd; padding:10px; border-radius:8px; background-color:#f8f9fa;"><b>{pdata["name"]}</b><br><span style="color:green;">${pdata["balance"]:,}</span><br><small>{bet_info}</small></div>', unsafe_allow_html=True)

time.sleep(1)
st.rerun()
