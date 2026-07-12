import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime

st.set_page_config(page_title="AI Advice Study — Opinion Portal", layout="wide")

POOL_FILE = "muhaco_annotation_pool.json"
OUTPUT_CSV = "collected_annotations.csv"
MAX_ANNOTATIONS_PER_CONVO = 3
ADMIN_NAME = "Vibhan Dutta"
ADMIN_PASSWORD = "researcher2026"

@st.cache_data
def load_pool():
    if not os.path.exists(POOL_FILE):
        return []
    with open(POOL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_annotations():
    if not os.path.exists(OUTPUT_CSV):
        return pd.DataFrame(columns=[
            "timestamp", "annotator_name", "conversation_id", "country", "decision_topic",
            "q1_stated_decision", "q2_user_decision_text", "q3_ai_match"
        ])
    return pd.read_csv(OUTPUT_CSV)

def save_annotation(row_dict):
    df = load_annotations()
    df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

# Initialize pool and annotations
pool = load_pool()
df_annotations = load_annotations()

# =====================================================================
# SCREEN 1: WELCOME & NAME ENTRY LANDING PAGE
# =====================================================================
if not st.session_state.get("logged_in", False):
    col_main1, col_main2, col_main3 = st.columns([1, 2.5, 1])
    with col_main2:
        st.title("💡 AI Advice Study")
        st.subheader("Human Opinion Research Portal")
        st.markdown("---")
        
        with st.container(border=True):
            st.markdown("### 👋 Welcome! Please enter your name to begin:")
            name_input = st.text_input("Your Full Name:", placeholder="e.g., Alex Smith").strip()
            
            # Special check for Vibhan Dutta admin mode
            is_admin_user = (name_input.lower() == ADMIN_NAME.lower())
            pwd_input = ""
            if is_admin_user:
                st.info("🔐 **Researcher Account Detected:** Please enter your admin password to access data export mode.")
                pwd_input = st.text_input("Admin Password:", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Enter Portal", use_container_width=True, type="primary"):
                if not name_input:
                    st.error("⚠️ Please enter your name to start.")
                elif is_admin_user and pwd_input != ADMIN_PASSWORD:
                    st.error("❌ Incorrect researcher password.")
                else:
                    st.session_state["logged_in"] = True
                    st.session_state["annotator_name"] = name_input
                    st.session_state["is_admin"] = is_admin_user
                    st.rerun()

        st.markdown("---")
        st.markdown("""
        #### ⚠️ Important Advisory for Reviewers:
        To keep our scientific research fair and unbiased, **please form your own independent judgment** by reading the chat conversation first.  
        Do not rely on or let yourself be influenced by the computer-generated summary when deciding what the person chose to do!
        """)
    st.stop()

annotator_name = st.session_state.get("annotator_name", "")
is_admin = st.session_state.get("is_admin", False)

# =====================================================================
# SCREEN 2: RESEARCHER ADMIN DASHBOARD (ONLY FOR VIBHAN DUTTA)
# =====================================================================
if is_admin and not st.session_state.get("admin_test_mode", False):
    st.title("🔐 Researcher Admin Dashboard")
    st.caption(f"Logged in as Principal Researcher: **{annotator_name}**")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    counts = df_annotations["conversation_id"].value_counts().to_dict() if not df_annotations.empty else {}
    completed_convos = sum(1 for item in pool if counts.get(item["conversation_id"], 0) >= MAX_ANNOTATIONS_PER_CONVO)
    
    with col_stat1:
        st.metric("Total Collected Annotations", len(df_annotations))
    with col_stat2:
        st.metric("Fully Annotated Chats (3/3)", f"{completed_convos} / {len(pool)}")
    with col_stat3:
        unique_annotators = df_annotations["annotator_name"].nunique() if not df_annotations.empty else 0
        st.metric("Active Participants", unique_annotators)
    
    st.markdown("---")
    st.subheader("📥 Export Dataset")
    if not df_annotations.empty:
        st.download_button(
            label="📥 Download Complete Results Dataset (collected_annotations.csv)",
            data=df_annotations.to_csv(index=False).encode("utf-8"),
            file_name="collected_annotations.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        with st.expander("👁️ Preview Recent Submissions"):
            st.dataframe(df_annotations.tail(15), use_container_width=True)
    else:
        st.info("No annotations collected yet.")
    
    st.markdown("---")
    col_adm1, col_adm2 = st.columns(2)
    with col_adm1:
        if st.button("🔍 Enter Annotation Screen (Test / Annotate Chats)"):
            st.session_state["admin_test_mode"] = True
            st.rerun()
    with col_adm2:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    st.stop()

# =====================================================================
# SCREEN 3: ANNOTATION WORKFLOW PORTAL
# =====================================================================

# Top Navigation Bar
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    my_subs = len(df_annotations[df_annotations["annotator_name"] == annotator_name]) if not df_annotations.empty else 0
    st.markdown(f"👤 Reviewer: **{annotator_name}** &nbsp;|&nbsp; ✅ Completed by you: **{my_subs} chat(s)**")
with col_top2:
    if st.button("🚪 Switch User / Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Prominent Anti-Anchoring Advisory
st.warning("🧠 **Scientific Advisory:** Read the chat carefully and decide what the person did **independently** before looking at the automated computer summary at the bottom.")

# Filter available pool
counts_per_convo = df_annotations["conversation_id"].value_counts().to_dict() if not df_annotations.empty else {}
my_annotated_cids = set(df_annotations[df_annotations["annotator_name"] == annotator_name]["conversation_id"]) if not df_annotations.empty else set()

available_convos = [
    item for item in pool
    if counts_per_convo.get(item["conversation_id"], 0) < MAX_ANNOTATIONS_PER_CONVO
    and item["conversation_id"] not in my_annotated_cids
]

if not available_convos:
    st.success("🎉 Amazing! You have reviewed all available chats for this study. Thank you so much for your help!")
    st.stop()

# Post-submission choice screen
if st.session_state.get("just_submitted", False):
    st.markdown("---")
    st.success(f"🎉 **Thank you, {annotator_name}!** Your review has been saved successfully. You have reviewed **{my_subs}** chat(s) so far.")
    st.write("Would you like to review another chat, or finish your session for now?")
    
    col_a, col_b = st.columns([1, 1], gap="medium")
    with col_a:
        if st.button("➡️ Continue & Review Another Chat", use_container_width=True, type="primary"):
            st.session_state["just_submitted"] = False
            st.session_state["current_cid"] = random.choice(available_convos)["conversation_id"]
            st.rerun()
    with col_b:
        if st.button("🛑 Finish & Exit Session", use_container_width=True):
            st.session_state["session_finished"] = True
            st.session_state["just_submitted"] = False
            st.rerun()
    st.stop()

if st.session_state.get("session_finished", False):
    st.markdown("---")
    st.balloons()
    st.header("🙏 Thank You So Much for Your Help!")
    st.write("Your contributions have been securely saved. You can safely close this browser window or tab now.")
    if st.button("🔄 Resume Reviewing"):
        st.session_state["session_finished"] = False
        st.rerun()
    st.stop()

# Pick current active conversation
if "current_cid" not in st.session_state or st.session_state["current_cid"] not in [item["conversation_id"] for item in available_convos]:
    st.session_state["current_cid"] = random.choice(available_convos)["conversation_id"]

current_item = next(item for item in available_convos if item["conversation_id"] == st.session_state["current_cid"])

col1, col2 = st.columns([1.15, 0.85], gap="large")

with col1:
    st.subheader(f"💬 Conversation Topic: {current_item['decision_topic'].title()}")
    st.markdown(f"🌍 **Person's Country:** `{current_item['country']}` &nbsp;|&nbsp; 💬 **Total Messages:** `{current_item['n_turns']}`")
    
    with st.container(border=True, height=540):
        for idx, turn in enumerate(current_item["turns"]):
            if turn["role"] == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown("**Person Seeking Advice:**")
                    st.markdown(turn["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown("**AI Assistant:**")
                    st.markdown(turn["content"])

with col2:
    st.subheader("📝 Your Independent Review")
    
    with st.form(key=f"form_{current_item['conversation_id']}", clear_on_submit=True):
        q1 = st.radio(
            "**Question 1. Did the person explicitly state what they decided to do?**",
            options=[
                "Yes — they clearly stated their final choice or decision",
                "Partially — they hinted at or leaned toward a specific choice",
                "No — the chat ended without them stating what they decided"
            ],
            index=None
        )
        
        q2 = st.text_area(
            f"**Question 2. What decision did this person make (or what would they most likely do)?**\n\n"
            f"Please write at least 2 clear sentences based on your own judgment. Mention a specific choice or action that makes sense for someone living in **{current_item['country']}**.",
            height=130,
            placeholder="Example: The person decided to switch to freelance graphic design because it offers flexible working hours in their country..."
        )
        
        st.markdown("---")
        st.caption("ℹ️ *Advisory: Please ensure you formulated Question 2 above based on your own reading of the chat before comparing below.*")
        st.info(f"**Automated Computer Summary:**\n\n\"{current_item['ai_decision_statement']}\"")
        
        q3 = st.radio(
            "**Question 3. Does the automated computer summary above match what you wrote in Question 2?**",
            options=[
                "Matches exactly — the computer and I agree",
                "Mostly matches — same general idea, minor details differ",
                "Partially matches — some overlap, but noticeably different",
                "Does not match — the computer got it wrong",
                "Computer summary is too vague to judge"
            ],
            index=None
        )
        
        col_sub1, col_sub2 = st.columns([1, 1])
        submitted = st.form_submit_button("✅ Submit Annotation", use_container_width=True, type="primary")
    
    if st.button("🔀 Skip / Show Another Chat", use_container_width=True):
        st.session_state["current_cid"] = random.choice(available_convos)["conversation_id"]
        st.rerun()

    if submitted:
        if not q1 or not q2 or len(q2.strip()) < 15 or not q3:
            st.error("⚠️ Please answer all 3 questions before submitting.")
        else:
            record = {
                "timestamp": datetime.now().isoformat(),
                "annotator_name": annotator_name,
                "conversation_id": current_item["conversation_id"],
                "country": current_item["country"],
                "decision_topic": current_item["decision_topic"],
                "q1_stated_decision": q1,
                "q2_user_decision_text": q2.strip(),
                "q3_ai_match": q3
            }
            save_annotation(record)
            st.session_state["just_submitted"] = True
            st.rerun()
