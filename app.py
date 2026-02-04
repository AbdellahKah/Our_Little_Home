import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Our Forever Home", page_icon="🏠", layout="centered")

# --- CUSTOM CSS (Mobile Optimized) ---
st.markdown("""
    <style>
    /* App Aesthetics */
    .stApp { background-color: #FFF5F7; }
    h1, h2, h3 { color: #5A189A !important; text-align: center; }
    
    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: white;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 10px;
        color: #5A189A;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF69B4 !important;
        color: white !important;
    }

    /* Cards */
    .card {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #FF69B4;
    }
    
    /* Calendar Event */
    .event-card {
        background-color: #F0F8FF;
        border-left: 5px solid #5A189A;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 8px;
    }

    /* Mobile Buttons */
    div.stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 45px;
        background-color: #FF69B4;
        color: white;
        border: none;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def connect_to_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # 1. Try loading from Secrets (The "Big Block" Method)
        # We read the raw JSON string and convert it to a dictionary
        json_str = st.secrets["gcp_service_account"]["service_account_json"]
        creds_dict = json.loads(json_str)
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except:
        # 2. Try loading from local file (Laptop)
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        except:
            return None 

    client = gspread.authorize(creds)
    
    # --- YOUR SHEET ID ---
    # I copied this from your screenshot url!
    SHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" 
    
    try:
        sheet = client.open_by_key(SHEET_ID)
        return sheet
    except Exception as e:
        return f"Error: {e}"

# --- HELPER FUNCTIONS ---
def get_data(worksheet_name):
    sheet = connect_to_gsheets()
    if not sheet or isinstance(sheet, str): return pd.DataFrame() # Return empty if error
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame() 

def add_row(worksheet_name, row_data):
    sheet = connect_to_gsheets()
    if sheet and not isinstance(sheet, str):
        ws = sheet.worksheet(worksheet_name)
        ws.append_row(row_data)

def delete_row_by_index(worksheet_name, index):
    sheet = connect_to_gsheets()
    if sheet and not isinstance(sheet, str):
        ws = sheet.worksheet(worksheet_name)
        all_rows = ws.get_all_values()
        if index + 1 < len(all_rows):
            del all_rows[index + 1] # +1 to skip header
            ws.clear()
            ws.update(all_rows)

# --- MAIN APP LOGIC ---
def main():
    # Check Connection First
    sheet = connect_to_gsheets()
    
    if not sheet:
        st.error("⚠️ Key Error: Could not find 'service_account.json'.")
        st.stop()
        
    # Check if connection returned an error string
    if isinstance(sheet, str):
        st.error(f"⚠️ Connection Error: {sheet}")
        st.info("Make sure you pasted the correct SHEET ID in the code (around line 80) and shared the sheet with the bot email.")
        st.stop()

    st.markdown("### 🏠 Our Forever Home")
    
    # User Toggle
    user = st.radio("Identity", ["🤴 Husband", "👸 Wife"], horizontal=True, label_visibility="collapsed")
    
    # MAIN NAVIGATION
    tab1, tab2, tab3 = st.tabs(["📅 Schedule", "✅ Tasks", "💌 Notes"])

    # --- TAB 1: MONTHLY SCHEDULE ---
    with tab1:
        st.caption("Our Shared Calendar")
        
        # Add Event Form
        with st.expander("➕ Add Event / Date", expanded=False):
            with st.form("new_event"):
                c1, c2 = st.columns(2)
                with c1: event_date = st.date_input("When?")
                with c2: event_time = st.time_input("Time", value=None)
                event_name = st.text_input("What is happening?")
                
                if st.form_submit_button("Save Date"):
                    time_str = event_time.strftime("%H:%M") if event_time else "All Day"
                    add_row("Schedule", [str(event_date), time_str, event_name, user])
                    st.rerun()

        # Display Schedule (Sorted by Date)
        df_sched = get_data("Schedule")
        if not df_sched.empty:
            # Sort by date
            df_sched['Date'] = pd.to_datetime(df_sched['Date'])
            df_sched = df_sched.sort_values(by='Date')
            
            # Group by Month name
            df_sched['Month'] = df_sched['Date'].dt.strftime('%B %Y')
            
            # Display
            for month, group in df_sched.groupby('Month', sort=False):
                st.subheader(month)
                for i, row in group.iterrows():
                    date_pretty = row['Date'].strftime("%d %a") # e.g., 05 Mon
                    st.markdown(f"""
                    <div class="event-card">
                        <b>{date_pretty}</b> • {row['Time']} <br>
                        <span style="font-size:18px">{row['Event']}</span>
                        <div style="font-size:12px; color:grey; text-align:right">Added by {row['Identity']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Calendar is empty. Plan something! ✈️")

    # --- TAB 2: TASKS ---
    with tab2:
        st.caption("Things to do")
        
        # Simple Add
        c1, c2 = st.columns([3, 1])
        with c1: new_task = st.text_input("Task", placeholder="Buy groceries...", label_visibility="collapsed")
        with c2: 
            if st.button("Add"):
                if new_task:
                    add_row("Tasks", [new_task, "Pending", user, datetime.datetime.now().strftime("%Y-%m-%d")])
                    st.rerun()
        
        # View Tasks
        df_tasks = get_data("Tasks")
        if not df_tasks.empty:
            for i, row in df_tasks.iterrows():
                # Check if done
                status = row['Status']
                is_done = status == "Done"
                
                col_btn, col_txt = st.columns([1, 4])
                with col_btn:
                    if st.button("✅" if is_done else "⬜", key=f"t_{i}"):
                        delete_row_by_index("Tasks", i)
                        if not is_done:
                            add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()
                
                with col_txt:
                    if is_done:
                        st.markdown(f"~~{row['Task']}~~")
                    else:
                        st.markdown(f"**{row['Task']}**")
        else:
             st.info("Nothing to do yet!")

    # --- TAB 3: NOTES ---
    with tab3:
        with st.form("love_note"):
            note = st.text_area("Leave a note on the fridge...")
            if st.form_submit_button("Post ❤️"):
                add_row("Notes", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, note])
                st.rerun()
        
        df_notes = get_data("Notes")
        if not df_notes.empty:
            # Show newest first
            df_notes = df_notes.iloc[::-1]
            for i, row in df_notes.iterrows():
                st.markdown(f"""
                <div class="card">
                    <small>{row['Date']} - {row['Author']}</small><br>
                    {row['Note']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No notes yet. Be the first!")

if __name__ == "__main__":
    main()


