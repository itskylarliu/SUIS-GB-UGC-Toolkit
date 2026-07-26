import streamlit as st
import pandas as pd
import os
from google import genai

st.set_page_config(page_title="UGC Toolkit", page_icon="🎓", layout="wide")

# --- SIDEBAR ROLE SELECTION WITH PASSWORD PROTECTION ---
st.sidebar.title("🔐 Portal Access")
role_selection = st.sidebar.radio(
    "Select Your Role:", 
    ["Student Portal (Submit List)", "Counselor Admin Login"]
)

# --- 1. STUDENT VIEW (Clean, standalone portal) ---
if role_selection == "Student Portal (Submit List)":
    st.title("🎓 US Student Application Tracker")
    st.write("Please enter your name and your submitted US university application list below.")
    
    student_name = st.text_input("Your Full Name (e.g., Alex Liu):")
    
    st.markdown("### Your Application List")
    st.info("Fill out your universities below. When finished, click **Submit My Applications** at the bottom.")
    
    student_input_df = pd.DataFrame([
        {"University": "", "Major": "", "Round": "Regular Decision (RD)"},
        {"University": "", "Major": "", "Round": "Regular Decision (RD)"},
        {"University": "", "Major": "", "Round": "Regular Decision (RD)"}
    ])
    
    edited_student_df = st.data_editor(
        student_input_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Round": st.column_config.SelectboxColumn(
                "Application Round",
                options=[
                    "Early Decision 1 (ED1)",
                    "Early Action (EA)", 
                    "Early Decision 2 (ED2)", 
                    "Regular Decision (RD)", 
                ],
                required=True
            )
        }
    )
    
    if st.button("Submit My Applications ✅"):
        if student_name.strip() == "":
            st.warning("Please enter your Full Name before submitting.")
        else:
            valid_rows = edited_student_df[edited_student_df["University"].str.strip() != ""]
            if len(valid_rows) == 0:
                st.warning("Please fill in at least one university.")
            else:
                csv_file = "master_applications.csv"
                if not os.path.exists(csv_file):
                    master_df = pd.DataFrame(columns=["Student Name", "University", "Major", "Round", "Transcript Sent", "Rec Uploaded", "Decision Status"])
                else:
                    master_df = pd.read_csv(csv_file)
                
                new_records = []
                for _, row in valid_rows.iterrows():
                    new_records.append({
                        "Student Name": student_name.strip(),
                        "University": row["University"],
                        "Major": row["Major"],
                        "Round": row["Round"],
                        "Transcript Sent": "Pending",
                        "Rec Uploaded": "Pending",
                        "Decision Status": "Working On It"
                    })
                
                df_new_entries = pd.DataFrame(new_records)
                master_df = pd.concat([master_df, df_new_entries], ignore_index=True)
                master_df.to_csv(csv_file, index=False)
                
                st.success(f"Thank you, {student_name}! Successfully submitted {len(new_records)} application(s) to your counselor.")

# --- 2. COUNSELOR ADMIN VIEW (Protected by a Password) ---
else:
    st.sidebar.markdown("---")
    passcode_input = st.sidebar.text_input("Enter Counselor Passcode:", type="password")
    
    # Set your secret passcode here (change "gubei2026" to whatever password you want)
    SECRET_PASSCODE = "suisgubei"
    
    if passcode_input != SECRET_PASSCODE:
        st.title("🔒 Restricted Access")
        if passcode_input == "":
            st.warning("Please enter the counselor passcode in the sidebar to access the admin toolkit.")
        else:
            st.error("Incorrect passcode. Access denied.")
    else:
        # SUCCESS: Passcode is correct, unlock the full toolkit
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        csv_file = "master_applications.csv"
        
        st.title("🎓 UGC Counselor Master Toolkit & Tracker")
        
        tab1, tab2, tab3 = st.tabs([
            "Translation", 
            "Reference Letters", 
            "Master Application Tracker"
        ])

        # --- TAB 1: TRANSLATION ---
        with tab1:
            st.header("Translation Assistant")
            source_text = st.text_area("Paste text to translate:", height=200, key="c_trans")
            doc_type = st.selectbox("Document Type:", ["WeChat Official Post", "Parent Letter", "UGC Handbook"], key="c_doctype")
            lang_direction = st.selectbox("Direction:", ["English to Chinese", "Chinese to English"], key="c_lang")
            
            hidden_glossary = "- Always translate '上海协和双语高级中学' strictly as 'Shanghai United International School, Gubei Campus'."
            
            if st.button("Translate"):
                if source_text:
                    with st.spinner("Translating..."):
                        prompt = f"Translate text from {lang_direction} for a {doc_type}. Follow rule:\n{hidden_glossary}\nText:\n{source_text}"
                        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                        st.write(response.text)
                else:
                    st.warning("Please enter text.")

        # --- TAB 2: REFERENCE LETTERS ---
        with tab2:
            st.header("Reference Letter Drafter")
            st.write("Reference letter generator features go here...")

        # --- TAB 3: MASTER TRACKER ---
        with tab3:
            st.header("Master Application Tracking Dashboard")
            st.write("Review all student submissions, check off transcripts, recommendations, and decisions.")
            
            if os.path.exists(csv_file):
                master_df = pd.read_csv(csv_file)
            else:
                master_df = pd.DataFrame(columns=["Student Name", "University", "Major", "Round", "Transcript Sent", "Rec Uploaded", "Decision Status"])
            
            updated_master = st.data_editor(
                master_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Round": st.column_config.SelectboxColumn("Application Round", options=["Early Action (EA)", "Early Decision (ED)", "Regular Decision (RD)", "Hong Kong JUPAS", "Hong Kong Non-JUPAS", "Rolling"]),
                    "Transcript Sent": st.column_config.SelectboxColumn("Transcript Sent", options=["Pending", "Sent", "N/A"]),
                    "Rec Uploaded": st.column_config.SelectboxColumn("Rec Uploaded", options=["Pending", "Uploaded", "N/A"]),
                    "Decision Status": st.column_config.SelectboxColumn("Decision Status", options=["Working On It", "Submitted", "Accepted", "Deferred", "Rejected", "Waitlisted"])
                }
            )
            
            if st.button("💾 Save Master Tracker Changes"):
                updated_master.to_csv(csv_file, index=False)
                st.success("Master tracker database updated successfully!")
