import os
from typing import List, Dict, Optional, Sequence

import streamlit as st
from openai import OpenAI


def resolve_openai_api_key() -> str:
    """Return the OpenAI API key from env or Streamlit secrets, or stop the app."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key:
        st.error("Missing OPENAI_API_KEY. Set it in the environment or Streamlit secrets.")
        st.stop()
    return api_key


def resolve_model_name(default: str = "gpt-4o-mini") -> str:
    """Choose the model from env/secrets or fall back to the provided default."""
    model = os.getenv("OPENAI_MODEL")
    if not model and "OPENAI_MODEL" in st.secrets:
        model = st.secrets["OPENAI_MODEL"]
    return model or default


def resolve_system_prompt(default: str) -> str:
    """Load custom system prompt from env/secrets or use the provided default."""
    prompt = os.getenv("DEFAULT_SQL_SYSTEM")
    if not prompt and "DEFAULT_SQL_SYSTEM" in st.secrets:
        prompt = st.secrets["DEFAULT_SQL_SYSTEM"]
    return prompt or default


def resolve_vector_store_ids() -> List[str]:
    """Fetch vector store IDs from env/secrets; return an empty list if none found."""
    raw = os.getenv("VECTOR_STORE_IDS")
    if not raw and "VECTOR_STORE_IDS" in st.secrets:
        raw = st.secrets["VECTOR_STORE_IDS"]

    if not raw:
        return []

    if isinstance(raw, (list, tuple)):
        ids = [item.strip() for item in raw if isinstance(item, str) and item.strip()]
    else:
        ids = [item.strip() for item in str(raw).split(",") if item.strip()]

    return ids


def format_history(messages: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Convert chat history into the structure required by the Responses API."""
    formatted = []
    for message in messages:
        role = message["role"]
        content_type = "output_text" if role == "assistant" else "input_text"
        formatted.append(
            {
                "role": role,
                "content": [
                    {
                        "type": content_type,
                        "text": message["content"],
                    }
                ],
            }
        )
    return formatted


def call_model(
    client: OpenAI,
    model: str,
    history: List[Dict[str, str]],
    prompt: str,
    system_prompt: Optional[str] = None,
    max_output_tokens: Optional[int] = 200,
    vector_store_ids: Optional[Sequence[str]] = None,
) -> tuple[str, Optional[object], bool]:
    """Call the Responses API with prior history plus the latest prompt."""
    conversation = []
    if system_prompt:
        conversation.append(
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt,
                    }
                ],
            }
        )

    conversation.extend(format_history(history))
    conversation.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": prompt,
                }
            ],
        }
    )

    tool_resources = {}
    if vector_store_ids:
        conversation.append({
        "role": "user",
        "content": [{"type":"input_text",
                     "text":"If needed, briefly use file_search to confirm column names/units, then write one SQL."}]
    })
        tools=[{"type": "file_search", "vector_store_ids": list(vector_store_ids)}]
    
    print("Tools: ", tools)

    response_kwargs = {
        "model": model,
        "input": conversation,
        "max_output_tokens": max_output_tokens,
        "tools": tools or None,
    }


    response = client.responses.create(**response_kwargs)
    print("Response: ", response)
    answer = getattr(response, "output_text", "")
    usage = getattr(response, "usage", None)
    return answer, usage


def main() -> None:
    api_key = resolve_openai_api_key()
    model_name = resolve_model_name()
    system_prompt = resolve_system_prompt("")
    vector_store_ids = resolve_vector_store_ids()
    print("Vector store IDs: ", vector_store_ids)
    client = OpenAI(api_key=api_key)

    st.title("💬 AI SQL Writer - Responses API")
    st.caption(f"Model: {model_name}")
    if vector_store_ids:
        st.sidebar.success("Vector search enabled")
    else:
        st.sidebar.info("No vector store attached")

    if "run_count" not in st.session_state:
        st.session_state.run_count = 0
    st.session_state.run_count += 1

    print(f"Run #{st.session_state.run_count}")
    print("Session state before:", dict(st.session_state))
    if "messages" not in st.session_state:
        st.session_state.messages = []

    print("Session state after init:", dict(st.session_state))

    if st.sidebar.button("🔁 Reset conversation"):
        st.session_state.messages = []
        st.rerun()

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    if prompt := st.chat_input("Ask me to write or debug SQL..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        try:
            #### to slice only for 6 newest messages to send to the model for saving tokens
            context_window = 6
            prior_messages = st.session_state.messages[:-1][-context_window:]
            
            answer, usage = call_model(
                client,
                model_name,
                prior_messages,
                prompt,
                system_prompt=system_prompt,
                max_output_tokens=300,
                vector_store_ids=vector_store_ids,
            )
            if usage:
                input_tokens = getattr(usage, "input_text_tokens", None) or getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_text_tokens", None) or getattr(usage, "output_tokens", None)
                total_tokens = getattr(usage, "total_tokens", None)

                if input_tokens is not None:
                    st.sidebar.write(f"Input tokens: {input_tokens}")
                if output_tokens is not None:
                    st.sidebar.write(f"Output tokens: {output_tokens}")
                if total_tokens is not None:
                    st.sidebar.write(f"Total tokens: {total_tokens}")

        except Exception as exc:  # noqa: BLE001 - surface any OpenAI/HTTP error cleanly
            answer = f"⚠️ Error calling OpenAI: {exc}"

        if not answer:
            answer = "⚠️ No response received, please try again."

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").markdown(answer)


if __name__ == "__main__":
    main()
