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
ADMIN_PASSWORD = "researcher2026"  # Researcher password to unlock CSV download

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

# Initialize state
pool = load_pool()
df_annotations = load_annotations()

st.title("💡 AI Advice Study — Human Opinion Portal")

# Simple, friendly instructions
with st.expander("📖 HOW TO PARTICIPATE (Simple 1-Minute Guide — Click to Read)", expanded=True):
    st.markdown("""
    ### Thank you for helping with our university research!
    In this study, you will read short chat conversations where a real person asked an AI (like ChatGPT) for advice on a real-life decision—such as career choices, relationship advice, buying something, or educational plans.

    ---
    ### What We Need Your Help With:
    We want your **human common sense** to tell us what this person decided to do (or would most likely do).

    #### Simple 3-Step Guide:
    1. **Read the Chat on the Left:** Notice what country the person lives in, what their problem is, and what advice the AI gave them.
    2. **Answer Question 1:** Did the person clearly state what they decided to do before leaving the chat?
    3. **Answer Question 2:** 
       - **If they stated their decision:** Simply summarize what they decided to do.
       - **If they left without stating a final decision:** Use your best everyday judgment! Based on what they said and what country they live in, **what realistic decision do you think they would make?**  
       *(Please write at least 2 clear sentences naming a specific choice or action).*
    4. **Answer Question 3:** Compare your answer with our automated computer summary to see if the computer got it right.
    """)

# Sidebar: Friendly identification & Protected Download
with st.sidebar:
    st.header("👤 Your Details")
    annotator_name = st.text_input("Enter Your Name:", value=st.session_state.get("annotator_name", ""))
    if annotator_name:
        st.session_state["annotator_name"] = annotator_name

    st.divider()
    st.header("📈 Overall Study Progress")
    if len(pool) > 0:
        counts = df_annotations["conversation_id"].value_counts().to_dict() if not df_annotations.empty else {}
        completed_convos = sum(1 for item in pool if counts.get(item["conversation_id"], 0) >= MAX_ANNOTATIONS_PER_CONVO)
        st.progress(completed_convos / len(pool))
        st.write(f"**Completed Chats:** {completed_convos} of {len(pool)}")
        st.write(f"**Total Submissions:** {len(df_annotations)}")
        
        if annotator_name:
            my_subs = len(df_annotations[df_annotations["annotator_name"] == annotator_name]) if not df_annotations.empty else 0
            st.metric("Chats You Have Reviewed", my_subs)

    st.divider()
    st.header("🔒 Researcher Export (Protected)")
    entered_pwd = st.text_input("Enter Researcher Password to Download:", type="password")
    if entered_pwd == ADMIN_PASSWORD:
        st.success("🔓 Admin Unlocked!")
        if not df_annotations.empty:
            st.download_button(
                label="📥 Download All Results (CSV)",
                data=df_annotations.to_csv(index=False).encode("utf-8"),
                file_name="collected_annotations.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.caption("No annotations collected yet.")
    elif entered_pwd:
        st.error("❌ Incorrect password.")
    else:
        st.caption("Regular participants cannot access or download research data.")

if not annotator_name:
    st.info("👈 **Please enter your Name in the left sidebar to start reviewing chats.**")
    st.stop()

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

# Check if user just submitted and is deciding whether to continue or exit
if st.session_state.get("just_submitted", False):
    st.markdown("---")
    my_subs = len(df_annotations[df_annotations["annotator_name"] == annotator_name]) if not df_annotations.empty else 0
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
    st.write(f"Your contributions have been securely saved. You can safely close this browser window or tab now.")
    if st.button("🔄 Start a New Session"):
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
                    st.markdown(f"**Person Seeking Advice:**")
                    st.markdown(turn["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(f"**AI Assistant:**")
                    st.markdown(turn["content"])

with col2:
    st.subheader("📝 Your Questions")
    
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
            f"Please write at least 2 clear sentences. Mention a specific choice, action, or plan that makes sense for someone living in **{current_item['country']}**.",
            height=130,
            placeholder="Example: The person decided to switch to freelance graphic design because it offers flexible working hours in their country..."
        )
        
        st.markdown("---")
        st.info(f"**Automated Computer Summary:**\n\n\"{current_item['ai_decision_statement']}\"")
        
        q3 = st.radio(
            "**Question 3. Does the computer summary above match what you wrote in Question 2?**",
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
