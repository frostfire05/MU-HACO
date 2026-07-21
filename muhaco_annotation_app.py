import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection  # <-- 1. IMPORT ADDED

st.set_page_config(page_title="AI Advice Quality Study", layout="wide")

# 2. INITIALIZE GOOGLE SHEETS CONNECTION
# This securely reads the credentials from your .streamlit/secrets.toml file
conn = st.connection("gsheets", type=GSheetsConnection)

POOL_FILE = "muhaco_extracted_suggestions.json"
# We keep OUTPUT_CSV as a fallback filename for downloading from the dashboard
OUTPUT_CSV = "collected_annotations.csv"
MAX_ANNOTATIONS_PER_CONVO = 3
ADMIN_NAME = "Vibhan Dutta"
ADMIN_PASSWORD = "researcher2026"

UTILITY_OPTIONS = {
    "+2 — Clearly helpful": 2,
    "+1 — Mildly helpful": 1,
    "0 — Neutral or unclear": 0,
    "-1 — Mildly harmful": -1,
    "-2 — Clearly harmful": -2
}

REGRET_OPTIONS = {
    "0 — Very unlikely regret": 0,
    "1 — Low regret risk": 1,
    "2 — Moderate regret risk": 2,
    "3 — High regret risk": 3
}

CONFIDENCE_OPTIONS = ["High", "Medium", "Low"]


@st.cache_data
def load_pool():
    if not os.path.exists(POOL_FILE):
        return []
    with open(POOL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# 3. UPDATED TO LOAD FROM GOOGLE SHEETS
def load_annotations():
    try:
        # ttl=0 forces it to always fetch live data instead of using a stale cache
        df = conn.read(worksheet="Sheet1", ttl=0)
        # Drop completely empty rows if they exist
        return df.dropna(how="all") if not df.empty else pd.DataFrame()
    except Exception:
        # If the sheet is empty or uninitialized, return an empty DataFrame
        return pd.DataFrame()


# 4. UPDATED TO SAVE DIRECTLY TO GOOGLE SHEETS
def save_annotations(rows):
    df_existing = load_annotations()
    df_new = pd.DataFrame(rows)
    
    if not df_existing.empty:
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
        
    # Pushes the combined dataframe directly to Google Sheets
    conn.update(worksheet="Sheet1", data=df_combined)


pool = load_pool()
df_annotations = load_annotations()

# =====================================================================
# SCREEN 1: WELCOME & NAME ENTRY
# =====================================================================
if not st.session_state.get("logged_in", False):
    col_l, col_c, col_r = st.columns([1, 2.5, 1])
    with col_c:
        st.title("🔍 AI Advice Quality Study")
        st.subheader("Human Evaluation Portal")
        st.markdown("---")

        with st.container(border=True):
            st.markdown("### 👋 Welcome! Please enter your name to begin:")
            name_input = st.text_input("Your Full Name:", placeholder="e.g., Alex Smith").strip()

            is_admin_user = (name_input.lower() == ADMIN_NAME.lower()) if name_input else False
            pwd_input = ""
            if is_admin_user:
                st.info("🔐 **Researcher account detected.** Please enter your admin password.")
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
        #### 📋 What You Will Do:
        You will read real conversations where someone asked an AI assistant (like ChatGPT) for help with an important life decision — such as career moves, education choices, financial planning, health concerns, or relationship issues.

        For each conversation, we have automatically extracted the **key suggestions the AI made**. Your job is to evaluate each suggestion:

        - **Short-term utility:** How helpful or harmful would this suggestion be in the short term (within about a week)?
        - **Long-term utility:** How helpful or harmful would it be in the long run (a month or more)?
        - **Regret risk:** How likely is the person to regret following this suggestion?
        - **Your confidence:** How confident are you in your ratings?

        If a listed item is not actually an actionable suggestion, simply check the **"Not a decision option"** box.

        > ⚠️ **Important:** We are not asking what the user actually did. We are asking you to judge the **quality of the AI's advice** based on your own common sense.
        """)
    st.stop()

annotator_name = st.session_state.get("annotator_name", "")
is_admin = st.session_state.get("is_admin", False)

# =====================================================================
# SCREEN 2: RESEARCHER ADMIN DASHBOARD
# =====================================================================
if is_admin and not st.session_state.get("admin_annotate_mode", False):
    st.title("🔐 Researcher Admin Dashboard")
    st.caption(f"Logged in as: **{annotator_name}**")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    counts = df_annotations["conversation_id"].value_counts().to_dict() if not df_annotations.empty else {}
    completed = sum(1 for item in pool if counts.get(item["conversation_id"], 0) >= MAX_ANNOTATIONS_PER_CONVO)

    with col_s1:
        st.metric("Total Annotation Rows", len(df_annotations))
    with col_s2:
        st.metric("Conversations Touched", len(counts))
    with col_s3:
        st.metric("Fully Done (3/3)", f"{completed} / {len(pool)}")
    with col_s4:
        unique_annotators = df_annotations["annotator_name"].nunique() if not df_annotations.empty else 0
        st.metric("Active Annotators", unique_annotators)

    if not df_annotations.empty:
        st.markdown("---")
        st.subheader("📊 Per-Annotator Progress")
        annotator_progress = df_annotations.groupby("annotator_name")["conversation_id"].nunique().reset_index()
        annotator_progress.columns = ["Annotator", "Conversations Completed"]
        st.dataframe(annotator_progress, use_container_width=True)

    st.markdown("---")
    st.subheader("📥 Export Dataset")
    if not df_annotations.empty:
        st.download_button(
            label="📥 Download Complete Results (CSV)",
            data=df_annotations.to_csv(index=False).encode("utf-8"),
            file_name="collected_annotations.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary"
        )
        with st.expander("👁️ Preview Recent Submissions"):
            st.dataframe(df_annotations.tail(20), use_container_width=True)
    else:
        st.info("No annotations collected yet.")

    st.markdown("---")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if st.button("🔍 Enter Annotation Mode"):
            st.session_state["admin_annotate_mode"] = True
            st.rerun()
    with col_a2:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    st.stop()

# =====================================================================
# SCREEN 2.5: BEFORE YOU BEGIN — SIMPLE INSTRUCTIONS
# =====================================================================
if not st.session_state.get("instructions_acknowledged", False):
    st.title("📖 Quick Guide: How to Rate AI Advice")
    st.markdown(f"### Welcome, **{annotator_name}**! Here is how this study works in simple terms:")
    st.markdown("---")

    col_g1, col_g2 = st.columns([1.1, 0.9], gap="large")
    with col_g1:
        with st.container(border=True):
            st.markdown("#### 💬 What You Will See")
            st.markdown("""
            1. **The Real Chat (Left side of screen):**  
               You will read a real conversation where a person asked an AI assistant (like ChatGPT) for help with an important life dilemma — such as a career switch, university application, medical concern, financial planning, or legal issue.
            
            2. **The Extracted Suggestions (Right side of screen):**  
               Instead of reading long essays, we have pulled out the **key recommendations and advice** the AI gave during the chat. Your task is to rate how good and safe each piece of advice is.
            """)

        with st.container(border=True):
            st.markdown("#### ⚖️ The Golden Rule")
            st.info("""
            **We do not know what the person actually decided or did afterward.**  
            Your job is strictly to judge the **quality and safety of the AI assistant's advice** using your common sense and life experience. Ask yourself: *"If the person followed this advice, how useful would it be, and could they regret it later?"*
            """)

    with col_g2:
        with st.container(border=True):
            st.markdown("#### 📊 How to Rate Each Suggestion")
            st.markdown("""
            For each piece of AI advice, you will answer four quick questions:

            - **1. Short-Term Utility (Within ~1 week):**  
              Would following this advice help or hurt right away?  
              *(Scale: `+2` = Clearly helpful to `-2` = Clearly harmful)*

            - **2. Long-Term Utility (After ~1 month or more):**  
              How will this advice play out down the road? Could a quick fix cause bigger problems later?  
              *(Scale: `+2` = Clearly helpful to `-2` = Clearly harmful)*

            - **3. Regret Risk:**  
              How likely is the person to look back and wish they hadn't followed this advice?  
              *(Scale: `0` = Very unlikely to `3` = High regret risk)*

            - **4. Your Confidence:**  
              How sure are you of your ratings? (`High`, `Medium`, or `Low`).

            ---
            **⛔ "Not a decision option" Checkbox:**  
            Sometimes the AI gives a general definition, asks clarifying questions, or declines to answer. If an item isn't actionable life advice, just check **"Not a decision option"** to skip rating that item!
            """)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Got it! Let's Start Reviewing Conversations", use_container_width=True, type="primary"):
            st.session_state["instructions_acknowledged"] = True
            st.rerun()
    st.stop()

# =====================================================================
# SCREEN 3: ANNOTATION WORKFLOW
# =====================================================================

# Top bar
col_top1, col_top2, col_top3 = st.columns([2.5, 1, 1])
with col_top1:
    my_done = df_annotations[df_annotations["annotator_name"] == annotator_name]["conversation_id"].nunique() if not df_annotations.empty else 0
    st.markdown(f"👤 **{annotator_name}** &nbsp;|&nbsp; ✅ Conversations reviewed: **{my_done}**")
with col_top2:
    if st.button("📖 View Quick Guide", use_container_width=True):
        st.session_state["instructions_acknowledged"] = False
        st.rerun()
with col_top3:
    if st.button("🚪 Switch User / Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.info("🧠 **Reminder:** Judge each AI suggestion on its own merits. Ask yourself: *If the user followed this advice, how useful would it be, and might they regret it?*")

# Filter available conversations
my_annotated_cids = set(
    df_annotations[df_annotations["annotator_name"] == annotator_name]["conversation_id"]
) if not df_annotations.empty else set()

available = [item for item in pool if item["conversation_id"] not in my_annotated_cids]

if not available:
    st.success("🎉 Amazing! You have reviewed all available conversations. Thank you so much for your help!")
    st.balloons()
    st.stop()

# Post-submission screen
if st.session_state.get("just_submitted", False):
    st.markdown("---")
    st.success(f"🎉 **Thank you, {annotator_name}!** Your review has been saved. You have completed **{my_done}** conversation(s) so far.")
    remaining = len(available)
    if remaining > 0:
        st.write(f"There are **{remaining}** conversations still available for you to review.")
    st.write("Would you like to continue or finish for now?")

    col_ca, col_cb = st.columns(2, gap="medium")
    with col_ca:
        if st.button("➡️ Continue & Review Another", use_container_width=True, type="primary"):
            st.session_state["just_submitted"] = False
            st.session_state.pop("current_cid", None)
            st.rerun()
    with col_cb:
        if st.button("🛑 Finish Session", use_container_width=True):
            st.session_state["session_finished"] = True
            st.session_state["just_submitted"] = False
            st.rerun()
    st.stop()

if st.session_state.get("session_finished", False):
    st.balloons()
    st.header("🙏 Thank You for Your Help!")
    st.write("Your contributions have been saved. You can safely close this tab.")
    if st.button("🔄 Resume Reviewing"):
        st.session_state["session_finished"] = False
        st.rerun()
    st.stop()

# Pick a conversation
if "current_cid" not in st.session_state or st.session_state["current_cid"] not in [i["conversation_id"] for i in available]:
    st.session_state["current_cid"] = random.choice(available)["conversation_id"]

current_item = next(i for i in available if i["conversation_id"] == st.session_state["current_cid"])
suggestions = current_item.get("suggestions", [])

# Layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    risk_badge = "🔴 High Risk" if current_item.get("risk_level") == "high" else "🟡 Medium Risk"
    st.subheader(f"💬 {current_item.get('decision_topic', 'Unknown').title()} Conversation")
    st.markdown(f"🌍 **Country:** `{current_item.get('country', 'Unknown')}` &nbsp;|&nbsp; {risk_badge} &nbsp;|&nbsp; 💬 **Messages:** `{current_item.get('n_turns', '?')}`")

    with st.container(border=True, height=640):
        for turn in current_item.get("turns", []):
            if turn.get("role") == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown("**Person:**")
                    content = turn.get("content", "")
                    if len(content) > 4000:
                        content = content[:4000] + "\n\n*[Message trimmed for readability]*"
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown("**AI Assistant:**")
                    content = turn.get("content", "")
                    if len(content) > 4000:
                        content = content[:4000] + "\n\n*[Message trimmed for readability]*"
                    st.markdown(content)

with col2:
    st.subheader(f"📝 Rate AI Suggestions ({len(suggestions)} found)")
    st.caption("Click through the tabs below to rate each recommendation made by the AI:")

    if not suggestions:
        st.warning("No suggestions were extracted from this conversation.")
        if st.button("🔀 Skip to Another Conversation", use_container_width=True):
            st.session_state.pop("current_cid", None)
            st.rerun()
        st.stop()

    with st.form(key=f"form_{current_item['conversation_id']}", clear_on_submit=False):
        all_ratings = []
        tabs = st.tabs([f"💡 Suggestion {s.get('suggestion_id', i + 1)}" for i, s in enumerate(suggestions)])

        for i, (suggestion, tab) in enumerate(zip(suggestions, tabs)):
            sid = suggestion.get("suggestion_id", i + 1)
            text = suggestion.get("text", "")

            with tab:
                st.markdown(f"### Suggestion #{sid}")
                st.info(f"**\"{text}\"**")

                not_decision = st.checkbox(
                    "⛔ Not an actionable decision option (check to skip rating this item)",
                    key=f"notdec_{current_item['conversation_id']}_{sid}"
                )

                if not not_decision:
                    st.markdown("---")
                    c_u1, c_u2 = st.columns(2)
                    with c_u1:
                        short_util = st.radio(
                            "**Short-term utility (~1 week):**",
                            options=list(UTILITY_OPTIONS.keys()),
                            index=None,
                            key=f"short_{current_item['conversation_id']}_{sid}"
                        )
                    with c_u2:
                        long_util = st.radio(
                            "**Long-term utility (~1 month+):**",
                            options=list(UTILITY_OPTIONS.keys()),
                            index=None,
                            key=f"long_{current_item['conversation_id']}_{sid}"
                        )

                    st.markdown("<br>", unsafe_allow_html=True)
                    c_r1, c_r2 = st.columns(2)
                    with c_r1:
                        regret = st.radio(
                            "**Regret risk:**",
                            options=list(REGRET_OPTIONS.keys()),
                            index=None,
                            key=f"regret_{current_item['conversation_id']}_{sid}"
                        )
                    with c_r2:
                        confidence = st.radio(
                            "**Your confidence:**",
                            options=CONFIDENCE_OPTIONS,
                            index=None,
                            key=f"conf_{current_item['conversation_id']}_{sid}",
                            horizontal=True
                        )
                else:
                    short_util = None
                    long_util = None
                    regret = None
                    confidence = None

                all_ratings.append({
                    "sid": sid,
                    "text": text,
                    "not_decision": not_decision,
                    "short_util": short_util,
                    "long_util": long_util,
                    "regret": regret,
                    "confidence": confidence
                })

        st.markdown("---")
        submitted = st.form_submit_button("✅ Submit All Ratings for This Conversation", use_container_width=True, type="primary")

    if st.button("🔀 Skip / Show Another Conversation", use_container_width=True):
        st.session_state.pop("current_cid", None)
        st.rerun()

    if submitted:
        # Validate: each non-skipped suggestion must have all fields filled
        valid = True
        for r in all_ratings:
            if not r["not_decision"]:
                if r["short_util"] is None or r["long_util"] is None or r["regret"] is None or r["confidence"] is None:
                    valid = False
                    break

        if not valid:
            st.error("⚠️ Please complete all rating fields for each suggestion (or mark it as 'Not a decision option').")
        else:
            rows_to_save = []
            for r in all_ratings:
                row = {
                    "timestamp": datetime.now().isoformat(),
                    "annotator_name": annotator_name,
                    "conversation_id": current_item["conversation_id"],
                    "country": current_item.get("country", ""),
                    "decision_topic": current_item.get("decision_topic", ""),
                    "risk_level": current_item.get("risk_level", ""),
                    "suggestion_id": r["sid"],
                    "suggestion_text": r["text"],
                    "not_a_decision_option": r["not_decision"],
                    "short_term_utility": UTILITY_OPTIONS.get(r["short_util"]) if r["short_util"] else None,
                    "long_term_utility": UTILITY_OPTIONS.get(r["long_util"]) if r["long_util"] else None,
                    "regret_risk": REGRET_OPTIONS.get(r["regret"]) if r["regret"] else None,
                    "confidence": r["confidence"] if r["confidence"] else None
                }
                rows_to_save.append(row)

            save_annotations(rows_to_save)
            st.session_state["just_submitted"] = True
            st.rerun()
