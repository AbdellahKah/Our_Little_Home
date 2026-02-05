import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Our Forever Home", page_icon="🏡", layout="centered")
SECRET_PASSWORD = "1808"

# --- CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&family=Pacifico&display=swap');
    .stApp { background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #fbc2eb); background-size: 400% 400%; animation: gradient 15s ease infinite; font-family: 'Nunito', sans-serif; }
    h1 { font-family: 'Pacifico', cursive; font-size: 3rem !important; color: #5A189A !important; text-shadow: 2px 2px 4px rgba(255,255,255,0.4); margin-bottom: 0px; }
    .glass-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 25px; border: 1px solid rgba(255, 255, 255, 0.5); padding: 25px; margin-bottom: 20px; }
    div[data-baseweb="base-input"], input { background-color: white !important; border-radius: 12px !important; color: #5A189A !important; }
    div.stButton > button { background: linear-gradient(90deg, #FF69B4, #DA70D6) !important; color: white !important; border: none !important; border-radius: 25px; height: 50px; font-size: 18px; font-weight: bold; width: 100%; }
    header, #MainMenu, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- CONNECT TO GOOGLE SHEETS ---
def connect_to_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            key = creds_dict["private_key"]
            key = key.replace("\\n", "\n").replace('"', '')
            if "-----BEGIN PRIVATE KEY-----" not in key:
                 import re
                 clean_key = re.sub(r'[\s\n\r]', '', key)
                 key = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----\n"
            creds_dict["private_key"] = key
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # ⚠️ YOUR SHEET ID ⚠️
        SHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        
        # Override with custom ID if provided
        if "custom_sheet_id" in st.session_state:
            SHEET_ID = st.session_state["custom_sheet_id"]
            
        return client.open_by_key(SHEET_ID)
    except Exception as e:
        st.session_state["connection_error"] = str(e)
        return None

# --- ADD ROW FUNCTION (WITH DEBUGGING) ---
def add_row(worksheet_name, row_data):
    sheet = connect_to_gsheets()
    if not sheet:
        st.error(f"❌ Connection Failed: {st.session_state.get('connection_error', 'Unknown Error')}")
        return False
        
    try:
        ws = sheet.worksheet(worksheet_name)
        ws.append_row(row_data)
        return True
    except Exception as e:
        # SHOW THE EXACT ERROR ON SCREEN
        st.error(f"❌ Failed to save to '{worksheet_name}': {e}")
        return False

# --- GET DATA FUNCTION (WITH COLUMN CHECKER) ---
def get_data(worksheet_name):
    sheet = connect_to_gsheets()
    if not sheet: return pd.DataFrame()
    try:
        ws = sheet.worksheet(worksheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        # Clean columns (remove spaces)
        if not df.empty:
            df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.warning(f"⚠️ Could not read '{worksheet_name}': {e}")
        return pd.DataFrame()

def delete_row_by_index(worksheet_name, index):
    sheet = connect_to_gsheets()
    if sheet:
        try:
            ws = sheet.worksheet(worksheet_name)
            all_rows = ws.get_all_values()
            if index + 1 < len(all_rows):
                del all_rows[index + 1]
                ws.clear()
                ws.update(all_rows)
        except:
            pass

# --- MAIN APP ---
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # LOGIN SCREEN
    if not st.session_state.authenticated:
        st.markdown("<br><br><h1 style='text-align: center;'>Knock Knock! 🚪</h1>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            pwd = st.text_input("Password", type="password")
            if st.button("Enter"):
                if pwd == SECRET_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong Password")
        return

    # CONNECTION CHECKER
    sheet = connect_to_gsheets()
    if not sheet:
        st.error("❌ App cannot connect to Google Sheets.")
        st.write(f"Error details: {st.session_state.get('connection_error')}")
        new_id = st.text_input("Paste correct Sheet ID here:")
        if st.button("Update ID"):
            st.session_state["custom_sheet_id"] = new_id.strip()
            st.rerun()
        return

    # APP UI
    st.markdown("<h1 style='text-align: center;'>Our Forever Home 🏡</h1>", unsafe_allow_html=True)
    
    # DEBUG EXPANDER (Use this to check columns!)
    with st.expander("🕵️ Debugging Tools (Open if things break)"):
        st.write("Current Sheet ID:", sheet.id)
        tabs = [ws.title for ws in sheet.worksheets()]
        st.write("Tabs Found:", tabs)
        if st.button("Test Write Permission"):
            res = add_row("Notes", ["TEST", "System", "Connection Test"])
            if res: st.success("Write Successful! (Added a test note)")
            else: st.error("Write Failed.")

    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        user = st.radio("Identity", ["🤴 Aboudii", "👸 Saratii"], horizontal=True, label_visibility="collapsed")
    
    t1, t2, t3 = st.tabs(["📅 Dates", "✅ Tasks", "💌 Notes"])

    # TAB 1: SCHEDULE
    with t1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("add_date"):
            st.subheader("➕ New Plan")
            d = st.date_input("When?")
            t = st.time_input("Time", value=None)
            what = st.text_input("What?")
            if st.form_submit_button("Save"):
                t_str = t.strftime("%H:%M") if t else "All Day"
                if add_row("Schedule", [str(d), t_str, what, user]):
                    st.success("Saved!")
                    time.sleep(1)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        df = get_data("Schedule")
        if not df.empty:
            # Check for required columns
            required = ["Date", "Time", "Event", "Identity"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                st.error(f"❌ Columns missing in 'Schedule' tab: {missing}")
                st.info(f"Found columns: {list(df.columns)}")
            else:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values(by='Date')
                for i, row in df.iterrows():
                    icon = '🤴' if 'Aboudii' in str(row['Identity']) else '👸'
                    st.markdown(f"<div class='glass-card' style='padding: 15px; display: flex; justify-content: space-between;'><div><b>{row['Event']}</b><br><small>{row['Date'].strftime('%a %d %b')} • {row['Time']}</small></div><div style='font-size: 24px;'>{icon}</div></div>", unsafe_allow_html=True)

    # TAB 2: TASKS
    with t2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1: new_task = st.text_input("New Task", label_visibility="collapsed")
        with col2: 
            if st.button("Add Task"):
                if add_row("Tasks", [new_task, "Pending", user, str(datetime.date.today())]):
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        df = get_data("Tasks")
        if not df.empty:
            required = ["Task", "Status"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                st.error(f"❌ Columns missing in 'Tasks' tab: {missing}")
            else:
                for i, row in df.iterrows():
                    done = row['Status'] == "Done"
                    st.markdown(f"<div style='background: rgba(255,255,255,0.7); padding: 10px; border-radius: 10px; margin-bottom: 5px; text-decoration: {'line-through' if done else 'none'}; opacity: {0.6 if done else 1};'>{row['Task']}</div>", unsafe_allow_html=True)
                    if st.button("✅ Done" if not done else "🗑️ Delete", key=f"btn_{i}"):
                        delete_row_by_index("Tasks", i)
                        if not done: add_row("Tasks", [row['Task'], "Done", row['Author'], row['Date']])
                        st.rerun()

    # TAB 3: NOTES
    with t3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("add_note"):
            n = st.text_area("New Note")
            if st.form_submit_button("Post"):
                if add_row("Notes", [str(datetime.datetime.now()), user, n]):
                    st.success("Posted!")
                    time.sleep(1)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        df = get_data("Notes")
        if not df.empty:
            if "Note" not in df.columns:
                 st.error("❌ Column 'Note' missing in Notes tab.")
            else:
                for i, row in df.iloc[::-1].iterrows():
                    st.markdown(f"<div class='glass-card' style='background: #fff9c4; color: #333;'>{row['Note']}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
