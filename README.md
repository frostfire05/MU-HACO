# MU-HACO Human Opinion Portal (AI Advice Study)

A lightweight, user-friendly Python Streamlit portal for collecting human annotations on real human-AI decision-making conversations. Designed to be accessible and easily readable for students and participants from any academic background (zero technical or CS jargon).

---

## ✨ Features
1. **Dynamic Quota Tracking (Max 3 Annotators per Chat):**
   Automatically tracks submissions in `collected_annotations.csv`. Once 3 different people review a chat, it is automatically retired from the active pool.
2. **True Randomization:**
   Serves conversations in a random order so annotators don't see items in a fixed sequence.
3. **LLM Comparison Display:**
   Displays the automated computer summary (`ai_decision_statement`) clearly so human annotators can directly evaluate and compare whether the AI prediction was accurate.
4. **Jargon-Free & Beginner Friendly:**
   Formatted with clean chat bubbles (`🧑 Person Seeking Advice` vs `🤖 AI Assistant`) and simple plain-English instructions.

---

