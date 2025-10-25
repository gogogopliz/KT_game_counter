import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Kill Team 2025 Scorer", layout="wide")

# --- Helpers ---
def init_session():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        # Basic match state
        st.session_state.turn = 1
        st.session_state.players = {
            "A": {
                "name": "Player A",
                "cp": 0,
                "crit": 0,
                "tac": 0,
                "kills": 0,
                "enemy_initial": 6,
                "kill_ops_points": 0,
                "initiative_cards": [],
                "final_bonus": 0
            },
            "B": {
                "name": "Player B",
                "cp": 0,
                "crit": 0,
                "tac": 0,
                "kills": 0,
                "enemy_initial": 6,
                "kill_ops_points": 0,
                "initiative_cards": [],
                "final_bonus": 0
            }
        }
        # default kill ops table (rows = enemy_initial sizes, cols = killed count)
        # A simple default for enemy sizes 4..10 and killed 0..10 with example values (editable)
        data = {}
        for init_size in range(4, 13):
            # values for killed 0..init_size
            data[init_size] = {k: max(0, min(4, int(round((k/init_size)*4)))) for k in range(0, init_size+1)}
        st.session_state.kill_ops_table = data
        # Match settings
        st.session_state.tac_op_choice = None
        st.session_state.primary_choice = None
        st.session_state.revealed = False
        st.session_state.history = []

init_session()

# --- Side configuration panel ---
with st.sidebar.expander("Match setup & options", expanded=True):
    st.markdown("## Match setup")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.players["A"]["name"] = st.text_input("Player A name", value=st.session_state.players["A"]["name"], key="nameA")
    with col2:
        st.session_state.players["B"]["name"] = st.text_input("Player B name", value=st.session_state.players["B"]["name"], key="nameB")

    st.markdown("---")
    st.markdown("### Pre-game secret selections (set at start)")
    # Tac Op mission selection (visible later)
    tac_options = ["Hold Ground", "Secure Objective", "Sabotage", "Assassinate", "Recon"]  # example labels; user can customize
    st.session_state.tac_op_choice = st.selectbox("Choose the Tac Op mission for this match (will be hidden until end)", options=["(none)"]+tac_options, index=0, key="tacselect")
    st.markdown("**Primary secret wager**: choose which scoring type you are betting on (secret). At end, you will earn half (rounded up) of that category if you chose it.")
    st.session_state.primary_choice = st.selectbox("Primary wager (secret)", options=["(none)","Crit Ops","Tac Ops","Kill Ops"], index=0, key="primaryselect")
    st.markdown("---")

    st.markdown("### Kill Ops table editor")
    st.markdown("Edit the grid values to match the official Games Workshop table. Rows = enemy initial size. Columns = killed count.")
    # Create a DataFrame view for editing one enemy_initial at a time
    enemy_sizes = sorted(list(st.session_state.kill_ops_table.keys()))
    chosen_row = st.selectbox("Edit table row (enemy initial size)", options=enemy_sizes, index=0, key="table_row")
    row = st.session_state.kill_ops_table[chosen_row].copy()
    df = pd.DataFrame.from_dict(row, orient="index", columns=["points"])
    df.index.name = "killed"
    edited = st.data_editor(df, num_rows="fixed")
    # Save changes back
    st.session_state.kill_ops_table[chosen_row] = {int(idx): int(edited.loc[idx,"points"]) for idx in edited.index}
    st.markdown("---")
    st.markdown("Buttons:")
    if st.button("Reset match"):
        init_session()
        st.experimental_rerun()

    if st.button("Finalize match (calculate final scores)"):
        # finalize: calculate kill ops for both, determine +1 bonus
        for k in ["A","B"]:
            p = st.session_state.players[k]
            p["kill_ops_points"] = calculate_kill_ops_points(p["enemy_initial"], p["kills"], st.session_state.kill_ops_table)
        a = st.session_state.players["A"]["kill_ops_points"]
        b = st.session_state.players["B"]["kill_ops_points"]
        if a > b:
            st.session_state.players["A"]["final_bonus"] = 1
            st.session_state.players["B"]["final_bonus"] = 0
        elif b > a:
            st.session_state.players["B"]["final_bonus"] = 1
            st.session_state.players["A"]["final_bonus"] = 0
        else:
            st.session_state.players["A"]["final_bonus"] = 0
            st.session_state.players["B"]["final_bonus"] = 0
        st.session_state.revealed = True
        st.success("Match finalized. Secrets revealed in main view.")

    st.markdown("---")
    st.markdown("Export / Import match state")
    if st.button("Export match JSON"):
        st.download_button("Download match JSON", data=json.dumps({
            "turn": st.session_state.turn,
            "players": st.session_state.players,
            "kill_ops_table": st.session_state.kill_ops_table,
            "tac_op_choice": st.session_state.tac_op_choice,
            "primary_choice": st.session_state.primary_choice
        }, indent=2), file_name="killteam_match.json", mime="application/json")

    upload = st.file_uploader("Import match JSON", type=["json"])
    if upload is not None:
        try:
            j = json.load(upload)
            st.session_state.turn = j.get("turn",1)
            st.session_state.players = j.get("players", st.session_state.players)
            st.session_state.kill_ops_table = j.get("kill_ops_table", st.session_state.kill_ops_table)
            st.session_state.tac_op_choice = j.get("tac_op_choice", st.session_state.tac_op_choice)
            st.session_state.primary_choice = j.get("primary_choice", st.session_state.primary_choice)
            st.success("Imported match state.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to import: {e}")

# --- Functions used in sidebar finalize button ---
def calculate_kill_ops_points(enemy_initial, killed, table):
    enemy_initial = int(enemy_initial)
    killed = int(killed)
    row = table.get(enemy_initial, None)
    if row is None:
        return 0
    # clamp killed to available keys
    killed = max(0, min(killed, max(row.keys())))
    return int(row.get(killed, 0))

# --- Main layout ---
st.title("Kill Team 2025 â Match Scorer (PWA / Streamlit)")
st.markdown("Use this page on mobile/tablet. Most controls live in the player panels.")

# Turn control and initiative modal simulation
st.markdown(f"### Current Turn: {st.session_state.turn}")

col1, col2, col3 = st.columns([1,1,2])
with col1:
    if st.button("Previous turn") and st.session_state.turn > 1:
        st.session_state.turn -= 1
with col2:
    if st.button("Next turn"):
        # On next turn: open initiative choice prompt
        winner = st.radio("Who won the initiative this turn? (choose then press Apply)", options=[st.session_state.players["A"]["name"], st.session_state.players["B"]["name"]], key=f"win_choice_{st.session_state.turn}")
        if st.button("Apply initiative result"):
            winner_key = "A" if winner == st.session_state.players["A"]["name"] else "B"
            loser_key = "B" if winner_key == "A" else "A"
            # apply CP
            st.session_state.players[winner_key]["cp"] = st.session_state.players[winner_key].get("cp",0) + 1
            st.session_state.players[loser_key]["cp"] = st.session_state.players[loser_key].get("cp",0) + 2
            # loser gains an initiative-card slot (we show generic cards the loser can choose from)
            # We'll add a default set if none exist as placeholders
            st.session_state.players[loser_key]["initiative_cards"].append({"type": "+1", "used": False, "id": f"{st.session_state.turn}_{len(st.session_state.players[loser_key]['initiative_cards'])}"})

            # Crit/Tac automatic progression: 0 on turn 1, +2 for each subsequent turn
            # We set current allowed maxima based on turn number
            # No automatic assignment of crit/tac; user must mark them manually, but we will enforce limits
            st.session_state.turn += 1
            st.experimental_rerun()

with col3:
    st.markdown("**Quick controls**")
    for k in ["A","B"]:
        p = st.session_state.players[k]
        colA, colB = st.columns(2)
    st.markdown("---")

# Player panels
def player_panel(player_key):
    p = st.session_state.players[player_key]
    st.subheader(p["name"])
    # CP controls
    cp_col1, cp_col2, cp_col3 = st.columns([1,1,2])
    with cp_col1:
        if st.button("+CP", key=f"pluscp_{player_key}"):
            p["cp"] += 1
        if st.button("-CP", key=f"minuscp_{player_key}"):
            p["cp"] = max(0, p["cp"] - 1)
    with cp_col2:
        new_cp = st.number_input("CP", value=p.get("cp",0), min_value=0, key=f"cp_input_{player_key}")
        p["cp"] = int(new_cp)
    # Crit / Tac
    max_per_turn = min(6, max(0, (st.session_state.turn-1)*2))  # 0 on turn1, +2 per subsequent
    c1, c2 = st.columns(2)
    with c1:
        new_crit = st.number_input("Crit Ops", min_value=0, max_value=6, value=p.get("crit", 0), key=f"crit_{player_key}")
        # Enforce that crit can't exceed max_per_turn
        if new_crit > max_per_turn:
            st.warning(f"Crit Ops cannot exceed {max_per_turn} at this point in the match.")
            new_crit = max_per_turn
        p["crit"] = int(new_crit)
    with c2:
        new_tac = st.number_input("Tac Ops", min_value=0, max_value=6, value=p.get("tac",0), key=f"tac_{player_key}")
        if new_tac > max_per_turn:
            st.warning(f"Tac Ops cannot exceed {max_per_turn} at this point in the match.")
            new_tac = max_per_turn
        p["tac"] = int(new_tac)

    # Kill ops inputs
    k1, k2, k3 = st.columns([1,1,2])
    with k1:
        enemy_init = st.number_input("Enemy initial size", min_value=1, value=p.get("enemy_initial",6), key=f"enemy_init_{player_key}")
        p["enemy_initial"] = int(enemy_init)
    with k2:
        killed = st.number_input("Killed", min_value=0, value=p.get("kills",0), key=f"killed_{player_key}")
        p["kills"] = int(killed)
    with k3:
        if st.button("Calculate Kill Ops", key=f"calc_killops_{player_key}"):
            p["kill_ops_points"] = calculate_kill_ops_points(p["enemy_initial"], p["kills"], st.session_state.kill_ops_table)
            st.success(f"Kill Ops for {p['name']}: {p['kill_ops_points']} points")

    # Initiative cards list
    st.markdown("**Initiative cards (tap to mark used)**")
    if "initiative_cards" not in p:
        p["initiative_cards"] = []
    # show as checkboxes
    cards = p["initiative_cards"]
    if not cards:
        st.info("No initiative cards yet (they are gained when you lose initiative).")
    else:
        for i, card in enumerate(cards):
            cols = st.columns([1,4,1])
            used = st.checkbox("Used", value=card.get("used", False), key=f"card_used_{player_key}_{i}")
            card["used"] = used
            st.write(f"Type: {card.get('type', '?')}")
            # If used and it's a "+n" card, apply effect? We leave actual effect application manual (CP etc.) but marking used is record

    st.markdown("---")
    # Show current subtotal
    subtotal = p.get("crit",0) + p.get("tac",0) + p.get("kill_ops_points",0)
    st.write(f"**Subtotal (Crit + Tac + KillOps):** {p.get('crit',0)} + {p.get('tac',0)} + {p.get('kill_ops_points',0)} = **{subtotal}**")
    st.write(f"**CP:** {p.get('cp',0)}  |  **Final bonus (kill tie):** {p.get('final_bonus',0)}")
    return p

left, right = st.columns(2)
with left:
    player_panel("A")
with right:
    player_panel("B")

# Bottom summary and secret reveal
st.markdown("## Match summary")
a = st.session_state.players["A"]
b = st.session_state.players["B"]

# Recalculate kill ops live (but keep explicit calculate option)
a["kill_ops_points"] = calculate_kill_ops_points(a["enemy_initial"], a["kills"], st.session_state.kill_ops_table)
b["kill_ops_points"] = calculate_kill_ops_points(b["enemy_initial"], b["kills"], st.session_state.kill_ops_table)

# Reveal tac op choice only after turn 4 finalized or if revealed
if st.session_state.revealed or st.session_state.turn > 4:
    st.markdown("### Tac Op mission (revealed)")
    st.write(st.session_state.tac_op_choice or "(none)")
else:
    st.markdown("### Tac Op mission (hidden until end of turn 4)")
    st.write("Hidden")

# Reveal primary wager at end
if st.session_state.revealed or st.session_state.turn > 4:
    st.markdown("### Primary wager (revealed)")
    st.write(st.session_state.primary_choice or "(none)")
    # apply primary bonus: half of chosen category rounded up
    def primary_bonus_for(player, choice):
        if not choice or choice == "(none)":
            return 0
        if choice == "Crit Ops":
            val = player.get("crit",0)
        elif choice == "Tac Ops":
            val = player.get("tac",0)
        elif choice == "Kill Ops":
            val = player.get("kill_ops_points",0)
        else:
            val = 0
        return math.ceil(val/2)
    a_primary = primary_bonus_for(a, st.session_state.primary_choice)
    b_primary = primary_bonus_for(b, st.session_state.primary_choice)
    st.write(f"{a['name']}: primary bonus = {a_primary} | {b['name']}: primary bonus = {b_primary}")
else:
    st.markdown("### Primary wager (hidden until end of turn 4)")
    st.write("Hidden")

# Total scores including primary and final bonus
def total_score(player):
    primary = 0
    if st.session_state.revealed or st.session_state.turn > 4:
        if st.session_state.primary_choice and st.session_state.primary_choice != "(none)":
            if st.session_state.primary_choice == "Crit Ops":
                primary = math.ceil(player.get("crit",0)/2)
            elif st.session_state.primary_choice == "Tac Ops":
                primary = math.ceil(player.get("tac",0)/2)
            elif st.session_state.primary_choice == "Kill Ops":
                primary = math.ceil(player.get("kill_ops_points",0)/2)
    return player.get("crit",0) + player.get("tac",0) + player.get("kill_ops_points",0) + player.get("final_bonus",0) + primary

st.write(f"**{a['name']} total:** {total_score(a)}  |  **{b['name']} total:** {total_score(b)}")

st.markdown("### Raw values")
st.json({"A": a, "B": b})

st.markdown("---")
st.info("This Streamlit app is a single-file prototype. To publish: push to GitHub and deploy on Streamlit Community Cloud. See README for instructions.")
