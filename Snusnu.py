import streamlit as st
import random
import time

# 1. SETUP SHARED STATE (This connects all players)
@st.cache_resource
def get_global_state():
    return {
        "players": {}, # {session_id: {"name": str, "balance": int, "bet": {}}}
        "history": [],
        "last_result": None,
        "is_spinning": False,
        "timer": 30 # Countdown for the next spin
    }

state = get_global_state()

# 2. ROULETTE LOGIC
ROULETTE_NUMBERS = {
    i: "red" if i in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36] 
    else "black" if i != 0 else "green" 
    for i in range(37)
}

def resolve_bets(winning_number):
    win_color = ROULETTE_NUMBERS[winning_number]
    for p_id, p_data in state["players"].items():
        bet = p_data.get("bet")
        if not bet: continue
        
        amt = bet["amount"]
        choice = bet["choice"]
        
        # Payout logic
        win = False
        if choice == str(winning_number):
            p_data["balance"] += amt * 35
            win = True
        elif choice in ["red", "black"] and choice == win_color:
            p_data["balance"] += amt * 2
            win = True
        
        if not win:
            p_data["balance"] -= amt
        
        p_data["bet"] = None # Reset bet for next round

# 3. UI LAYOUT
st.title("🎰 Live Multiplayer Roulette")

# Player Registration
if "my_id" not in st.session_state:
    st.session_state.my_id = str(random.randint(1000, 9999))

name = st.text_input("Enter your name to join:", key="name_input")
if name and st.session_state.my_id not in state["players"]:
    state["players"][st.session_state.my_id] = {"name": name, "balance": 1000, "bet": None}

# Game Info
if st.session_state.my_id in state["players"]:
    p = state["players"][st.session_state.my_id]
    st.sidebar.metric("Your Balance", f"${p['balance']}")
    
    # Betting Controls
    st.subheader("Place Your Bet")
    col1, col2 = st.columns(2)
    with col1:
        bet_amt = st.number_input("Amount", 10, p["balance"], step=10)
    with col2:
        bet_choice = st.selectbox("Bet On", ["red", "black"] + [str(i) for i in range(37)])
    
    if st.button("Place Bet"):
        state["players"][st.session_state.my_id]["bet"] = {"amount": bet_amt, "choice": bet_choice}
        st.success(f"Bet placed on {bet_choice}!")

# Live Table Status
st.divider()
st.write("### 👥 Players in Room")
for p_id, p_data in state["players"].items():
    status = "✅ Bet Placed" if p_data["bet"] else "⏳ Thinking..."
    st.write(f"**{p_data['name']}**: {status}")

# The "Live" Spinner (Simplified)
if st.button("🌀 DEBUG: Spin Wheel (Manual)"):
    with st.spinner("Wheel is spinning..."):
        time.sleep(2)
        res = random.randint(0, 36)
        state["last_result"] = res
        resolve_bets(res)
        state["history"].insert(0, f"{res} ({ROULETTE_NUMBERS[res]})")

if state["last_result"] is not None:
    color = "green" if state["last_result"] == 0 else ROULETTE_NUMBERS[state["last_result"]]
    st.header(f"Last Result: :{color}[{state['last_result']}]")

st.write("### 📜 History")
st.write(", ".join(state["history"][:10]))

# Auto-refresh helper
st.empty()
time.sleep(2)
st.rerun()
