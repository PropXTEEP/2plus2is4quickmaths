import streamlit as st
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="RPS Lobby", page_icon="🎮")

# --- SHARED STATE MANAGEMENT ---
class GameStore:
    def __init__(self):
        self.rooms = {}

    def get_active_rooms(self):
        # Returns a list of rooms that aren't full yet
        return [rid for rid, data in self.rooms.items() if data["p2"] is None]

    def create_room(self, room_id, player_name):
        if room_id in self.rooms:
            return False
        self.rooms[room_id] = {
            "p1": player_name, 
            "p2": None, 
            "p1_move": None, 
            "p2_move": None,
            "status": "waiting"
        }
        return True

    def join_room(self, room_id, player_name):
        room = self.rooms.get(room_id)
        if room and room["p2"] is None and room["p1"] != player_name:
            room["p2"] = player_name
            room["status"] = "playing"
            return True
        return False

    def make_move(self, room_id, role, move):
        if room_id in self.rooms:
            self.rooms[room_id][f"{role}_move"] = move

    def reset_game(self, room_id):
        if room_id in self.rooms:
            self.rooms[room_id]["p1_move"] = None
            self.rooms[room_id]["p2_move"] = None

@st.cache_resource
def get_store():
    return GameStore()

store = get_store()

# --- UI LOGIC ---
st.title("✂️ RPS Multiplayer Lobby")

if "role" not in st.session_state:
    st.subheader("Join the Arena")
    name = st.text_input("Enter your nickname", placeholder="e.g. Player1")
    
    if name:
        tab1, tab2 = st.tabs(["Join Existing Room", "Create New Room"])
        
        with tab1:
            rooms = store.get_active_rooms()
            if not rooms:
                st.info("No active rooms found. Why not create one?")
                if st.button("🔄 Refresh Lobby"):
                    st.rerun()
            else:
                for rid in rooms:
                    col_room, col_btn = st.columns([3, 1])
                    col_room.write(f"🏠 **{rid}** (Waiting for opponent...)")
                    if col_btn.button(f"Join", key=f"join_{rid}"):
                        if store.join_room(rid, name):
                            st.session_state.role = "p2"
                            st.session_state.name = name
                            st.session_state.room_id = rid
                            st.rerun()
                        else:
                            st.error("Could not join room.")

        with tab2:
            new_room_name = st.text_input("New Room Name", placeholder="e.g. TheDojo")
            if st.button("Create & Join"):
                if new_room_name:
                    if store.create_room(new_room_name, name):
                        st.session_state.role = "p1"
                        st.session_state.name = name
                        st.session_state.room_id = new_room_name
                        st.rerun()
                    else:
                        st.error("Room name already exists!")
                else:
                    st.warning("Please enter a room name.")

# --- GAME INTERFACE ---
else:
    room_id = st.session_state.room_id
    role = st.session_state.role
    room_data = store.rooms.get(room_id)

    if not room_data:
        st.error("Room no longer exists.")
        if st.button("Back to Lobby"):
            del st.session_state.role
            st.rerun()
    else:
        st.write(f"📍 Room: **{room_id}** | Player: **{st.session_state.name}**")
        
        if room_data["p2"] is None:
            st.warning("Waiting for an opponent to join...")
            time.sleep(2)
            st.rerun()
        
        else:
            opponent = room_data["p2"] if role == "p1" else room_data["p1"]
            st.success(f"Battle: **{st.session_state.name} vs {opponent}**")

            my_move = room_data[f"{role}_move"]
            opp_move = room_data["p2_move" if role == "p1" else "p1_move"]

            if my_move is None:
                st.subheader("Pick your weapon:")
                c1, c2, c3 = st.columns(3)
                if c1.button("🪨 Rock"): store.make_move(room_id, role, "Rock"); st.rerun()
                if c2.button("📄 Paper"): store.make_move(room_id, role, "Paper"); st.rerun()
                if c3.button("✂️ Scissors"): store.make_move(room_id, role, "Scissors"); st.rerun()

            elif opp_move is None:
                st.info(f"You played **{my_move}**. Waiting for {opponent}...")
                time.sleep(2)
                st.rerun()

            else:
                st.markdown("---")
                st.write(f"You: **{my_move}** | {opponent}: **{opp_move}**")
                
                # Winner Logic
                if my_move == opp_move:
                    st.info("It's a Draw!")
                elif (my_move == "Rock" and opp_move == "Scissors") or \
                     (my_move == "Paper" and opp_move == "Rock") or \
                     (my_move == "Scissors" and opp_move == "Paper"):
                    st.success("You Won!")
                    st.balloons()
                else:
                    st.error("You Lost!")

                if st.button("Next Round"):
                    store.reset_game(room_id)
                    st.rerun()
                
                if st.button("Exit to Lobby"):
                    # Basic cleanup (in a real app you'd remove the player from the room)
                    del st.session_state.role
                    st.rerun()
