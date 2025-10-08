import streamlit as st
from openai import OpenAI
import os

# Resolve API key from env or Streamlit secrets, fail gracefully if missing
api_key = os.getenv("OPENAI_API_KEY")
if not api_key and "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
if not api_key:
    st.error(
        "Missing OPENAI_API_KEY. Set it as an environment variable or add it to Streamlit secrets."
    )
    st.stop()

# Init OpenAI client
client = OpenAI(api_key=api_key)

# Use the Assistant you already created (with vector store attached)
# Prefer env/secrets if provided; fallback to hardcoded value
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
if not ASSISTANT_ID and "ASSISTANT_ID" in st.secrets:
    ASSISTANT_ID = st.secrets["ASSISTANT_ID"]
if not ASSISTANT_ID:
    ASSISTANT_ID = "asst_cluFh3dbHS6ynCg547O7e0XM"  # replace with your assistant_id

# Keep one thread per user session
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

st.title("💬 AI SQL Writer Assistant")
st.caption("Uses OpenAI Assistants API + your vector store")

# Display past messages
print("Session state: ", st.session_state)
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask me to write or debug SQL..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Send message to assistant
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
    )

    # Run the assistant with retrieval (since vector store is attached)
    run = client.beta.threads.runs.create_and_poll(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
    )

    # Fetch assistant reply
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        answer = messages.data[0].content[0].text.value
    else:
        answer = "⚠️ Something went wrong — try again."

    # Save + display assistant reply
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").markdown(answer)
