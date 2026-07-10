# app_dojo.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from data_dojo import KIDS, BEHAVIORS, MILESTONES

# ---- CONFIGURATION ----
st.set_page_config(
    page_title="Family Dojo Points Tracker",
    page_icon="🎯",
    layout="centered"
)

# Custom Styling (Adding Thermometer Progress Aesthetics)
st.markdown("""
    <style>
        div.stButton > button:first-child {
            background-color: #6366f1 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: bold !important;
        }
        .kid-card {
            background-color: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-bottom: 15px;
            text-align: center;
        }
        .thermometer-container {
            background-color: #e2e8f0;
            border-radius: 20px;
            position: relative;
            height: 30px;
            width: 100%;
            margin-top: 10px;
            overflow: hidden;
            border: 1px solid #cbd5e1;
        }
        .thermometer-fill {
            background: linear-gradient(90deg, #ff4b4b 0%, #6366f1 100%);
            height: 100%;
            border-radius: 20px;
            transition: width 0.5s ease-in-out;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Family Dojo Points Tracker")
st.write("Encouraging habits and tracking goals together!")
st.divider()

# ---- DATA STORAGE CORE ----
LOG_FILE = "dojo_points_log.csv"

def load_data():
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=["Timestamp", "Kid", "Action", "Category", "Points", "Notes"])

def get_totals(df):
    totals = {kid: 0 for kid in KIDS}
    if not df.empty:
        for kid in KIDS:
            totals[kid] = df[df["Kid"] == kid]["Points"].sum()
    return totals

df_log = load_data()
totals = get_totals(df_log)

# ---- NAVIGATION TABS ----
tab_dash, tab_add, tab_rewards, tab_history = st.tabs([
    "📊 Leaderboard & Thermometers", "⚡ Log Points", "🎁 Reward Milestones", "📜 History Log"
])

# ---- TAB 1: LEADERBOARD & THERMOMETERS ----
with tab_dash:
    st.header("Point Thermometers")
    st.write("Tracking progress toward the major 100-point milestone goal!")
    
    col1, col2 = st.columns(2)
    THERMOMETER_GOAL = 100  # Baseline thermometer capacity marker
    
    with col1:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader("👧 Ari")  # Updated to Girl Emoji
        st.metric(label="Total Balance", value=f"{totals['Ari']} pts")
        
        # Thermometer fill math
        ari_pct = min(max(float(totals['Ari']) / THERMOMETER_GOAL, 0.0), 1.0) * 100
        st.markdown(f"**Goal Progress: {int(ari_pct)}%**")
        st.markdown(f"""
            <div class="thermometer-container">
                <div class="thermometer-fill" style="width: {ari_pct}%;"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader("👦 AJ")   # Updated to Boy Emoji
        st.metric(label="Total Balance", value=f"{totals['AJ']} pts")
        
        # Thermometer fill math
        aj_pct = min(max(float(totals['AJ']) / THERMOMETER_GOAL, 0.0), 1.0) * 100
        st.markdown(f"**Goal Progress: {int(aj_pct)}%**")
        st.markdown(f"""
            <div class="thermometer-container">
                <div class="thermometer-fill" style="width: {aj_pct}%;"></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---- TAB 2: LOG POINTS (ADD / DEDUCT) ----
with tab_add:
    st.header("Adjust Dojo Points Balance")
    
    with st.form("points_form", clear_on_submit=True):
        selected_kid = st.radio("Select Child:", KIDS, horizontal=True)
        
        # ACTION SELECTION TO ADD OR DEDUCT
        action_type = st.radio("Action Type:", ["Award / Add Points 🟢", "Deduct / Remove Points 🔴"], horizontal=True)
        
        behavior_key = st.selectbox("Select Associated Behavior", list(BEHAVIORS.keys()))
        behavior_desc = BEHAVIORS[behavior_key]
        
        raw_points = st.number_input("Point Count", min_value=1, max_value=20, value=1, step=1)
        optional_notes = st.text_input("Notes / Context (e.g., 'Refused to clean room' or 'Shared toys beautifully')")
        
        submit_points = st.form_submit_button("Submit Points Adjustment")
        
        if submit_points:
            # Handle sign assignment based on action selection
            is_deduction = "Deduct" in action_type
            final_points = -abs(raw_points) if is_deduction else abs(raw_points)
            action_label = "Deduction" if is_deduction else "Award"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = pd.DataFrame([{
                "Timestamp": timestamp,
                "Kid": selected_kid,
                "Action": action_label,
                "Category": behavior_desc,
                "Points": final_points,
                "Notes": optional_notes
            }])
            
            if not os.path.isfile(LOG_FILE):
                new_entry.to_csv(LOG_FILE, index=False)
            else:
                new_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)
                
            if is_deduction:
                st.error(f"Logged: Removed {raw_points} points from {selected_kid}.")
            else:
                st.success(f"Logged: Added +{raw_points} points to {selected_kid}!")
            st.rerun()

# ---- TAB 3: REWARD MILESTONES ----
with tab_rewards:
    st.header("🎁 Prize Milestones")
    st.write("Track how close Ari and AJ are to unlocking their next reward targets!")
    
    selected_view = st.selectbox("Check milestone progress for:", KIDS)
    current_points = totals[selected_view]
    
    st.write(f"**{selected_view} has: {current_points} points**")
    
    for mile in MILESTONES:
        target = mile["points"]
        reward_text = mile["reward"]
        
        progress_pct = min(max(float(current_points) / float(target), 0.0), 1.0)
        status_emoji = "✅ UNLOCKED!" if current_points >= target else f"⏳ {target - current_points} pts away"
        
        with st.expander(f"🏅 {target} Points Target — {status_emoji}"):
            st.progress(progress_pct)
            st.write(f"**Prize Item:** {reward_text}")

# ---- TAB 4: HISTORY LOG ----
with tab_history:
    st.header("Activity History")
    if not df_log.empty:
        st.dataframe(df_log.iloc[::-1], use_container_width=True)
    else:
        st.info("No activity logged yet.")
