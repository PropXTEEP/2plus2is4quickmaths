import streamlit as st
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Multiplayer RPS", page_icon="✂️")

# --- SHARED STATE MANAGEMENT ---
# This class lives in the server's memory and is shared across ALL users
class GameStore:
    def __init__(self):
        self.rooms = {}

    def create_or_join(self, room_id, player_name):
        if room_id not in self.rooms:
            self.rooms[room_id] = {
                "p1": player_name, 
                "p2": None, 
                "p1_move": None, 
                "p2_move": None,
                "status": "waiting"
            }
            return "p1"
        else:
            room = self.rooms[room_id]
            if room["p2"] is None and room["p1"] != player_name:
                room["p2"] = player_name
                room["status"] = "playing"
                return "p2"
            elif room["p1"] == player_name:
                return "p1"
            elif room["p2"] == player_name:
                return "p2"
            else:
                return "full"

    def make_move(self, room_id, role, move):
        if room_id in self.rooms:
            self.rooms[room_id][f"{role}_move"] = move

    def get_room_state(self, room_id):
        return self.rooms.get(room_id, None)

    def reset_game(self, room_id):
        if room_id in self.rooms:
            self.rooms[room_id]["p1_move"] = None
            self.rooms[room_id]["p2_move"] = None

# Initialize the global shared state
@st.cache_resource
def get_store():
    return GameStore()

store = get_store()

# --- UI LOGIC ---
st.title("✂️ Rock Paper Scissors: Multiplayer")

# Step 1: Login / Room Selection
if "role" not in st.session_state:
    st.write("Enter a Room Name to join your friend.")
    c1, c2 = st.columns(2)
    name = c1.text_input("Your Name")
    room_id = c2.text_input("Room Name (e.g., 'Battle1')")
    
    if st.button("Join Game"):
        if name and room_id:
            role = store.create_or_join(room_id, name)
            if role == "full":
                st.error("Room is full!")
            else:
                st.session_state.role = role
                st.session_state.name = name
                st.session_state.room_id = room_id
                st.rerun()

# Step 2: The Game Interface
else:
    room_id = st.session_state.room_id
    role = st.session_state.role
    room_data = store.get_room_state(room_id)

    # Header
    st.write(f"Logged in as: **{st.session_state.name}** in Room: **{room_id}**")
    
    # Check if opponent is here
    if room_data["p2"] is None:
        st.warning("Waiting for an opponent to join this room name...")
        time.sleep(2) # Auto-refresh to check for opponent
        st.rerun()
    
    else:
        # Determine Opponent Name
        opponent = room_data["p2"] if role == "p1" else room_data["p1"]
        st.success(f"Playing against: **{opponent}**")

        # Logic: Has everyone moved?
        my_move = room_data[f"{role}_move"]
        opp_move = room_data[f"p2_move" if role == "p1" else "p1_move"]

        # 2a. Input Phase
        if my_move is None:
            st.subheader("Make your move!")
            col1, col2, col3 = st.columns(3)
            if col1.button("🪨 Rock", use_container_width=True):
                store.make_move(room_id, role, "Rock")
                st.rerun()
            if col2.button("📄 Paper", use_container_width=True):
                store.make_move(room_id, role, "Paper")
                st.rerun()
            if col3.button("✂️ Scissors", use_container_width=True):
                store.make_move(room_id, role, "Scissors")
                st.rerun()

        # 2b. Waiting Phase (I moved, opponent hasn't)
        elif my_move is not None and opp_move is None:
            st.info(f"You chose **{my_move}**. Waiting for {opponent}...")
            time.sleep(2) # Auto-refresh
            st.rerun()

        # 2c. Result Phase (Both moved)
        elif my_move is not None and opp_move is not None:
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("You", my_move)
            c2.metric(opponent, opp_move)
            
            # Determine Winner
            result = ""
            if my_move == opp_move:
                result = "It's a Tie! 🤝"
                st.info(result)
            elif (my_move == "Rock" and opp_move == "Scissors") or \
                 (my_move == "Paper" and opp_move == "Rock") or \
                 (my_move == "Scissors" and opp_move == "Paper"):
                result = "You Win! 🎉"
                st.balloons()
                st.success(result)
            else:
                result = "You Lose! 💀"
                st.error(result)

            if st.button("Play Again"):
                store.reset_game(room_id)
                st.rerun()
            
            # Auto-refresh so if opponent clicks "Play Again", I see it
            time.sleep(3) 
            st.rerun()
