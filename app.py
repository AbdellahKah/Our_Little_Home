import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os

# --- CONFIGURATION ---
# "centered" layout is better for mobile screens than "wide"
st.set_page_config(page_title="Our Forever Home", page_icon="🏡", layout="centered")
SECRET_PASSWORD = "1808"

# --- MOBILE OPTIMIZED CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&family=Pacifico&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Indie+Flower&display=swap');

    /* 1. VIEWPORT & TOUCH FIXES */
    /* Prevents blue highlight on tap */
    * { -webkit-tap-highlight-color: transparent; }
    
    /* Make inputs large enough to prevent iOS/Android auto-zoom (min 16px) */
    input, textarea, select { font-size: 16px !important; }

    /* BACKGROUND */
    .stApp {
        background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #fbc2eb);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        font-family: 'Nunito', sans-serif;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* TYPOGRAPHY */
    h1 { font-family: 'Pacifico', cursive; font-size: 2.2rem !important; color: #5A189A !important; text-align: center; margin-top: -20px; }
    h3 { font-family: 'Nunito', sans-serif; color: #5A189A !important; font-weight: 700; font-size: 1.2rem; }

    /* CONTAINERS */
    .glass-card { 
        background: rgba(255, 255, 255, 0.85); 
        backdrop-filter: blur(12px); 
        border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.5); 
        padding: 15px; 
        margin-bottom: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
    }

    /* WIDGET STYLING */
    div.stButton > button { 
        background: linear-gradient(90deg, #FF69B4, #DA70D6) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 25px; 
        height: 55px; /* Taller for thumbs */
        font-size: 18px; 
        font-weight: bold; 
        width: 100%; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Edit/Delete Small Buttons */
    div[data-testid="column"] button {
        background: white !important;
        border: 1px solid #ddd !important;
        height: 45px;
        width: 45px;
        border-radius: 50%;
        font-size: 20px;
        box-shadow: none !important;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: rgba(255,255,255,0.4); 
        border-radius: 50px; 
        padding: 5px; 
        gap: 5px; 
    }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; 
        border-radius: 40px; 
        background-color: transparent; 
        color: #5A189A; 
        font-weight: 700; 
        border: none; 
        flex-grow: 1; 
    }
    .stTabs [aria-selected="true"] { 
        background-color: #fff !important; 
        color: #FF69B4 !important; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
    }

    /* HIDE STREAMLIT CHROME */
    header, #MainMenu, footer {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
def connect_to_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Try Streamlit Secrets (Best for Cloud Hosting)
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            # Handle newline formatting in private key which often breaks in copy-paste
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            # 👇👇👇 YOUR SHEET ID IS HERE 👇👇👇
            return gspread.authorize(creds).open_by_key("1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ")
    except Exception as e:
        # st.write(f"Secrets Error: {e}") # Debug only
        pass

    # 2. Try Local File (Backup / Dev)
    try:
        if os.path.exists("service_account.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
            return gspread.authorize(creds).open_by_key("1y04dfrk53yPCm0MNU0OdiUMZlr41GhhxtXfgVDsBuoQ")
    except:
        return None
    
    return None

# --- ROBUST DATA FUNCTIONS ---
def get_data(worksheet_name):
    sheet = connect_to_gsheets()
    if not sheet: return pd.DataFrame()
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame() 

def add_row(worksheet_name, row_data):
    sheet = connect_to_gsheets()
    if not sheet:
        st.error("❌ Disconnected. Check Internet.")
        return False
    try:
        try:
            ws = sheet.worksheet(worksheet_name)
        except:
            ws = sheet.add_worksheet(title=worksheet_name, rows=100, cols=10)
            if worksheet_name == "Schedule":
                ws.append_row(["Date", "Time", "Event", "Identity"])
            elif worksheet_name == "Tasks":
                ws.append_row(["Task", "Status", "Author", "Date"])
            elif worksheet_name == "Notes":
                ws.append_row(["Date", "Author", "Note"])
        
        ws.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

def delete_specific_row(worksheet_name, row_number):
    sheet = connect_to_gsheets()
    if sheet:
        try:
            ws = sheet.worksheet(worksheet_name)
            ws.delete_rows(row_number)
            return True
        except:
            return False

def update_row(worksheet_name, row_number, new_data):
    sheet = connect_to_gsheets()
    if sheet:
        try:
            ws = sheet.worksheet(worksheet_name)
            cell_range = f"A{row_number}:D{row_number}"
            ws.update(cell_range, [new_data]) 
            return True
        except:
            return False

# --- SCREENS ---
def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Knock Knock! 🚪</h1>", unsafe_allow_html=True)
    st.write("") 
    
    # Use form to allow "Enter" key submission on mobile keyboards
    with st.form("login_form"):
        password = st.text_input("Enter the Secret Key:", type="password", placeholder="Shhh...")
        submitted = st.form_submit_button("Open Door 🔑", use_container_width=True)
        
        if submitted:
            if password == SECRET_PASSWORD:
                st.session_state.authenticated = True
                st.balloons()
                st.rerun()
            else:
                st.error("Wrong key! Are you a stranger? 😜")

def main_app():
    # --- CONNECTION CHECK ---
    # We do a quick check but don't block the UI immediately to make it feel faster
    
    st.markdown("<h1 style='text-align: center;'>Our Forever Home 🏡</h1>", unsafe_allow_html=True)
    
    # User toggle - Full width for easy tapping
    user = st.radio("Who are you?", ["🤴 Aboudii", "👸 Saratii"], horizontal=True, label_visibility="collapsed")
    st.write("") 
    
    tab1, tab2, tab3 = st.tabs(["📅 Dates", "✅ Tasks", "💌 Notes"])

    # --- TAB 1: DATES ---
    with tab1:
        with st.expander("➕ Plan a New Date", expanded=False):
            with st.form("new_event"):
                c1, c2 = st.columns(2)
                with c1: event_date = st.date_input("When?")
                with c2: event_time = st.time_input("Time", value=None)
                event_name = st.text_input("What is the plan?")
                
                if st.form_submit_button("Save to Calendar"):
                    time_str = event_time.strftime("%H:%M") if event_time else "All Day"
                    success = add_row("Schedule", [str(event_date), time_str, event_name, user])
                    if success:
                        st.toast("Saved!", icon="🎉")
                        time.sleep(1)
                        st.rerun()
        
        df = get_data("Schedule")
        if not df.empty and "Date" in df.columns:
            df['sheet_row'] = df.index + 2
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values(by='Date')
            df['Month'] = df['Date'].dt.strftime('%B')
            
            for month, group in df.groupby('Month', sort=False):
                st.markdown(f"<h3 style='margin: 15px 0 5px 0; padding-left: 5px;'>{month}</h3>", unsafe_allow_html=True)
                for i, row in group.iterrows():
                    icon = '🤴' if 'Aboudii' in str(row.get('Identity', '')) else '👸'
                    row_num = row['sheet_row']

                    # Custom Mobile Card Layout
                    with st.container():
                        col_main, col_act = st.columns([5, 1.5])
                        
                        with col_main:
                            st.markdown(
                                f"""
                                <div class='glass-card' style='border-left: 6px solid #5A189A; padding: 12px; margin-bottom: 5px;'>
                                    <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                                        <div>
                                            <div style='font-size: 18px; font-weight: bold; color: #5A189A; line-height: 1.2;'>{row.get('Event', 'Date')}</div>
                                            <div style='font-size: 13px; color: #666; margin-top: 4px;'>
                                                📅 {row['Date'].strftime('%a %d')} &nbsp; ⏰ {row.get('Time', '')}
                                            </div>
                                        </div>
                                        <div style='font-size: 22px; padding-left: 10px;'>{icon}</div>
                                    </div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        
                        # Actions (Edit/Delete) grouped tightly
                        with col_act:
                            st.write("") # Alignment spacer
                            if st.button("✏️", key=f"e_{row_num}"):
                                st.session_state[f"editing_{row_num}"] = not st.session_state.get(f"editing_{row_num}", False)
                            
                            if st.button("🗑️", key=f"d_{row_num}"):
                                delete_specific_row("Schedule", row_num)
                                st.rerun()

                    # Edit Form
                    if st.session_state.get(f"editing_{row_num}"):
                        with st.form(key=f"edit_form_{row_num}"):
                            st.caption(f"Editing: {row['Event']}")
                            e_date = st.date_input("Date", value=row['Date'])
                            try:
                                t_val = datetime.datetime.strptime(row['Time'], "%H:%M").time()
                            except:
                                t_val = None
                            e_time = st.time_input("Time", value=t_val)
                            e_name = st.text_input("Event", value=row['Event'])
                            
                            if st.form_submit_button("Update"):
                                new_time_str = e_time.strftime("%H:%M") if e_time else "All Day"
                                update_row("Schedule", row_num, [str(e_date), new_time_str, e_name, row['Identity']])
                                st.session_state[f"editing_{row_num}"] = False
                                st.rerun()
        else:
             st.info("No dates yet! Add one above.")

    # --- TAB 2: TASKS ---
    with tab2:
        with st.form("task_form", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            with c1: 
                new_task = st.text_input("Task", placeholder="Buy milk...", label_visibility="collapsed")
            with c2: 
                sub = st.form_submit_button("Add")
            
            if sub and new_task:
                add_row("Tasks", [new_task, "Pending", user, datetime.datetime.now().strftime("%Y-%m-%d")])
                st.rerun()
        
        df = get_data("Tasks")
        if not df.empty and "Task" in df.columns:
            for i, row in df.iterrows():
                is_done = row.get('Status', '') == "Done"
                # Visual styling based on status
                bg_color = "rgba(255,255,255,0.4)" if is_done else "rgba(255,255,255,0.85)"
                txt_deco = "line-through" if is_done else "none"
                opacity = "0.6" if is_done else "1.0"
                
                c_check, c_txt = st.columns([1, 5])
                with c_check:
                    # Using a button as a checkbox for better mobile touch target
                    btn_label = "✅" if is_done else "⬜"
                    if st.button(btn_label, key=f"tick_{i}"):
                        delete_specific_row("Tasks", i + 2)
                        # Toggle logic: if done -> delete; if not -> move to bottom as done
                        if not is_done: 
                            add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()
                
                with c_txt:
                    st.markdown(
                        f"""
                        <div style='background: {bg_color}; border-radius: 12px; padding: 12px; opacity: {opacity}; min-height: 45px; display: flex; align-items: center;'>
                            <span style='font-size: 16px; color: #333; text-decoration: {txt_deco}; font-weight: 600;'>{row['Task']}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        else:
             st.info("No tasks! You are free! 🕊️")

    # --- TAB 3: NOTES ---
    with tab3:
        with st.form("love_note"):
            note = st.text_area("Note", placeholder="Write something sweet...", height=100, label_visibility="collapsed")
            if st.form_submit_button("Post Note ❤️"):
                add_row("Notes", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, note])
                st.rerun()
        
        df = get_data("Notes")
        if not df.empty and "Note" in df.columns:
            df = df.iloc[::-1] # Newest first
            for i, row in df.iterrows():
                rotation = (i % 3) - 1.5 # Slight random tilt
                st.markdown(
                    f"""
                    <div class='glass-card' style='background: #fff9c4; transform: rotate({rotation}deg); border: none; margin-top: 10px;'>
                        <div style='font-size: 11px; color: #888; margin-bottom: 5px; display: flex; justify-content: space-between; border-bottom: 1px dashed #bbb; padding-bottom: 4px;'>
                            <span>{row.get('Date','')}</span>
                            <span style='color: #5A189A;'><b>{row.get('Author','')}</b></span>
                        </div>
                        <div style='font-family: "Indie Flower", cursive; font-size: 20px; color: #333; line-height: 1.3;'>
                            {row['Note']}
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

# --- APP ENTRY POINT ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_screen()
else:
    main_app()
