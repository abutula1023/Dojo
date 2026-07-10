# app_dojo.py
import streamlit as st
import os
from datetime import datetime
import pandas as pd
from data_dojo import KIDS, BEHAVIORS, MILESTONES

# ---- CONFIGURATION ----
st.set_page_config(
    page_title="Family Dojo Points Tracker",
    page_icon="🎯",
    layout="centered"
)

# Custom Styling
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

# ---- UNBREAKABLE DATA PARSER ----
LOG_FILE = "dojo_points_log.csv"

EMOJI_MAPPING = {
    "Ari": "👧 Ari",
    "AJ": "👦 AJ"
}

def load_data_safely():
    """An indestructible parser that cleans old bad data, emojis, and mixed commas/pipes on the fly."""
    history = []
    # Force absolute baseline totals
    totals = {"Ari": 0, "AJ": 0}
    
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("Timestamp|Kid|Action|Category|Points|Notes\n")
        return history, totals

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines[1:]: 
        clean_line = line.strip()
        if not clean_line:
            continue
        
        # Auto-detect if it's an old comma log or a new pipe log
        delimiter = "|" if "|" in clean_line else ","
        parts = clean_line.split(delimiter)
        
        if len(parts) >= 5:
            raw_kid = parts[1]
            # Absolute name extraction (ignoring old emojis or spaces)
            clean_kid = "Ari" if "Ari" in raw_kid else "AJ" if "AJ" in raw_kid else raw_kid.strip()
            
            try:
                pts = int(parts[4])
            except ValueError:
                pts = 0
                
            history.append({
                "Timestamp": parts[0], 
                "Kid": clean_kid, 
                "Action": parts[2], 
                "Category": parts[3], 
                "Points": pts, 
                "Notes": parts[5] if len(parts) > 5 else ""
            })
            
            # Tally up points safely
            if clean_kid in totals:
                totals[clean_kid] += pts
                
    return history, totals

# Read the file fresh every single time the page loads
history_log, totals = load_data_safely()

# ---- NAVIGATION TABS ----
tab_dash, tab_add, tab_rewards, tab_history = st.tabs([
    "📊 Leaderboard & Thermometers", "⚡ Log Points", "🎁 Reward Milestones", "📜 History Log"
])

# ---- TAB 1: LEADERBOARD & THERMOMETERS ----
with tab_dash:
    st.header("Point Thermometers")
    st.write("Tracking progress toward the major 100-point milestone goal!")
    
    col1, col2 = st.columns(2)
    THERMOMETER_GOAL = 100  
    
    with col1:
        st.markdown('<div class="kid-card">', unsafe_allow_html=True)
        st.subheader(EMOJI_MAPPING["Ari"])
        st.metric(label="Total Balance", value=f"{totals['Ari']} pts")
        
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
        st.subheader(EMOJI_MAPPING["AJ"])
        st.metric(label="Total Balance", value=f"{totals['AJ']} pts")
        
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
        kid_display = st.radio("Select Child:", [EMOJI_MAPPING["Ari"], EMOJI_MAPPING["AJ"]], horizontal=True)
        selected_kid = "Ari" if "Ari" in kid_display else "AJ"
        
        action_type = st.radio("Action Type:", ["Award / Add Points 🟢", "Deduct / Remove Points 🔴"], horizontal=True)
        behavior_key = st.selectbox("Select Associated Behavior", list(BEHAVIORS.keys()))
        behavior_desc = BEHAVIORS[behavior_key]
        raw_points = st.number_input("Point Count", min_value=1, max_value=20, value=1, step=1)
        optional_notes = st.text_input("Notes / Context")
        
        submit_points = st.form_submit_button("Submit Points Adjustment")
        
        if submit_points:
            is_deduction = "Deduct" in action_type
            final_points = -abs(raw_points) if is_deduction else abs(raw_points)
            action_label = "Deduction" if is_deduction else "Award"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_notes = str(optional_notes).replace("|", " ").replace("\n", " ")
            safe_category = str(behavior_desc).replace("|", " ")
            
            # Save strictly as clean text to the file
            log_line = f"{timestamp}|{selected_kid}|{action_label}|{safe_category}|{final_points}|{safe_notes}\n"
            
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
                
            # FORCE APP RELOAD so the screen updates instantly!
            st.rerun()

# ---- TAB 3: REWARD MILESTONES ----
with tab_rewards:
    st.header("🎁 Prize Milestones")
    st.write("Track how close Ari and AJ are to unlocking their next reward targets!")
    
    selected_view_display = st.selectbox("Check milestone progress for:", [EMOJI_MAPPING["Ari"], EMOJI_MAPPING["AJ"]])
    selected_view = "Ari" if "Ari" in selected_view_display else "AJ"
    
    current_points = totals[selected_view]
    
    st.write(f"**{selected_view_display} has: {current_points} points**")
    
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
    if history_log:
        # Reapply emojis dynamically just for the pretty log table
        display_list = []
        for row in history_log:
            display_list.append({
                "Timestamp": row["Timestamp"],
                "Kid": EMOJI_MAPPING.get(row["Kid"], row["Kid"]),
                "Action": row["Action"],
                "Category": row["Category"],
                "Points": row["Points"],
                "Notes": row["Notes"]
            })
        display_df = pd.DataFrame(display_list)
        st.dataframe(display_df.iloc[::-1], use_container_width=True)
    else:
        st.info("No activity logged yet.")
