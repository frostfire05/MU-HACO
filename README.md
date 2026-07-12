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

## 🚀 How to Run Locally

1. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Streamlit portal:
   ```bash
   streamlit run muhaco_annotation_app.py
   ```
3. Open `http://localhost:8501` in your web browser.

---

## 🌐 How to Host Free Online (Streamlit Community Cloud)

1. Upload these 4 files to a new GitHub repository:
   - `muhaco_annotation_app.py`
   - `muhaco_annotation_pool.json`
   - `requirements.txt`
   - `README.md`
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
3. Click **New App** → Select your repository → Main file path: `muhaco_annotation_app.py`.
4. Click **Deploy**! Share the public link with your colleagues.
