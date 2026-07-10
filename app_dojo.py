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

# Custom Color Styling (Fun Dojo Purple/Indigo Vibe)
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
            border-radius: 10px;
            border-left: 5px solid #6366f1;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Family Dojo Points")
st.write("Encouraging great habits every single day!")
st.divider()

# ---- DATA STORAGE CORE ----
LOG_FILE = "dojo_points_log.csv"

def load_data():
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=["Timestamp", "Kid", "Category", "Points", "Notes"])

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
    "📊 Leaderboard", "➕ Award Points", "🎁 Reward Milestones", "📜 History Log"
])

# ---- TAB 1: LEADERBOARD ----
with tab_dash:
    st.header("Current Standings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader("👦 Ari's Score")
        st.metric(label="Total Points", value=f"{totals['Ari']} pts")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader("👧 AJ's Score")
        st.metric(label="Total Points", value=f"{totals['AJ']} pts")
        st.markdown('</div>', unsafe_allow_html=True)

# ---- TAB 2: AWARD POINTS ----
with tab_add:
    st.header("Award Dojo Points")
    st.write("Select a category and log points for great behavior.")
    
    with st.form("points_form", clear_on_submit=True):
        selected_kid = st.radio("Who earned points?", KIDS, horizontal=True)
        
        behavior_key = st.selectbox("Select Behavior Category", list(BEHAVIORS.keys()))
        behavior_desc = BEHAVIORS[behavior_key]
        
        points_to_award = st.number_input("Amount of points", min_value=1, max_value=10, value=1, step=1)
        optional_notes = st.text_input("Notes / Specific Details (e.g., 'Cleaned bedroom beautifully!')")
        
        submit_points = st.form_submit_button("💥 Award Points!")
        
        if submit_points:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = pd.DataFrame([{
                "Timestamp": timestamp,
                "Kid": selected_kid,
                "Category": behavior_desc,
                "Points": points_to_award,
                "Notes": optional_notes
            }])
            
            if not os.path.isfile(LOG_FILE):
                new_entry.to_csv(LOG_FILE, index=False)
            else:
                new_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)
                
            st.success(f"Awesome! Logged +{points_to_award} points for {selected_kid} under '{behavior_key}'!")
            st.rerun()

# ---- TAB 3: REWARD MILESTONES ----
with tab_rewards:
    st.header("🎁 Prize Milestones")
    st.write("Track how close Ari and AJ are to unlocking their next reward targets!")
    
    selected_view = st.selectbox("Check milestone progress for:", KIDS)
    current_points = totals[selected_view]
    
    st.write(f"**{selected_view} has: {current_points} points**")
    
    # Render interactive progress matrix
    for mile in MILESTONES:
        target = mile["points"]
        reward_text = mile["reward"]
        
        # Calculate individual goal progression percentage
        progress_pct = min(float(current_points) / float(target), 1.0)
        
        status_emoji = "✅ UNLOCKED!" if current_points >= target else f"⏳ {target - current_points} pts away"
        
        with st.expander(f"🏅 {target} Points Target — {status_emoji}"):
            st.progress(progress_pct)
            st.write(f"**Prize Item:** {reward_text}")

# ---- TAB 4: HISTORY LOG ----
with tab_history:
    st.header("Activity History")
    if not df_log.empty:
        # Sort log to show newest entries first
        st.dataframe(df_log.iloc[::-1], use_container_width=True)
    else:
        st.info("No points logged yet. Head over to the 'Award Points' tab to get started!")
