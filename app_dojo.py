# app_dojo.py
import streamlit as st
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

# ---- NATIVE SAFEDATA RECOVERY ENGINE ----
LOG_FILE = "dojo_points_log.csv"

def parse_log_safely():
    """Reads logs line-by-line via raw string splits to avoid Pandas version mismatch panics"""
    raw_history = []
    totals = {kid: 0 for kid in KIDS}
    
    if not os.path.exists(LOG_FILE):
        # Construct header from scratch if file doesn't exist
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("Timestamp,Kid,Action,Category,Points,Notes\n")
        return raw_history, totals

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines[1:]: # Skip the CSV header string row
        clean_line = line.strip()
        if not clean_line:
            continue
        
        # Split tokens via standard comma delimiters
        parts = clean_line.split(",", 5)
        if len(parts) >= 5:
            # Reconstruct missing notes parameter dynamically if omitted
            notes = parts[5] if len(parts) == 6 else ""
            timestamp, kid, action, category, pts_str = parts[0], parts[1], parts[2], parts[3], parts[4]
            
            try:
                points_val = int(pts_str)
            except ValueError:
                points_val = 0
                
            raw_history.append({
                "Timestamp": timestamp, "Kid": kid, "Action": action, 
                "Category": category, "Points": points_val, "Notes": notes
            })
            
            if kid in totals:
                totals[kid] += points_val
                
    return raw_history, totals

# Compute operational totals
history_log, totals = parse_log_safely()

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
        st.subheader("👧 Ari")
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
        st.subheader("👦 AJ")
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
        selected_kid = st.radio("Select Child:", KIDS, horizontal=True)
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
            
            # Sanitize notes text to prevent raw breaking return characters
            safe_notes = str(optional_notes).replace(",", " ").replace("\n", " ")
            
            # Direct text injection bypasses Pandas parsing models completely
            log_line = f"{timestamp},{selected_kid},{action_label},{behavior_desc},{final_points},{safe_notes}\n"
            
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
                
            st.success(f"Successfully logged adjustment for {selected_kid}!")
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
    if history_log:
        import pandas as pd
        # Converted back to presentation-only table format so it reads smoothly
        display_df = pd.DataFrame(history_log)
        st.dataframe(display_df.iloc[::-1], use_container_width=True)
    else:
        st.info("No activity logged yet.")
