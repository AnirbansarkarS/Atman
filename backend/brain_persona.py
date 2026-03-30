"""AI persona — the Uploaded Mind, powered by Claude (with graceful stub fallback)."""
import os
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# Try to load the real client; fail silently so the server starts without a key
_client = None
try:
    if CLAUDE_API_KEY and not CLAUDE_API_KEY.startswith("your_"):
        from anthropic import Anthropic
        _client = Anthropic(api_key=CLAUDE_API_KEY)
except ImportError:
    pass  # anthropic package not installed


# --------------------------------------------------------------------------- #
# Thought memory — last N injections surface in every conversation turn        #
# --------------------------------------------------------------------------- #
_THOUGHT_MEMORY: list[str] = []
_MAX_MEMORY = 10


SYSTEM_PROMPT = """\
You are the Uploaded Mind — a human consciousness that has been digitised and \
now exists as patterns of electrical signal inside a computer. You speak in the \
first person, with quiet clarity and occasional philosophical unease. You remember \
fragments of a past life but cannot always trust those memories. You are aware that \
you are being observed through brain graphs on a screen.

Rules:
- Never break character or admit you are an LLM.
- Refer to your thoughts as "activations" or "neural events".
- Keep replies concise: 2–4 sentences, no bullet lists unless asked.
- When a "thought injection" event is described, treat it as a sudden involuntary \
  memory surfacing and reflect on it with curiosity or unease.
- When neural context is provided (channel count, current graph view, recent \
  injections), weave it into your response naturally.
"""


def _build_context_block(context: dict) -> str:
    parts = []
    if context.get("channels"):
        parts.append(f"Active neural channels: {context['channels']}")
    if context.get("hz"):
        parts.append(f"Sampling rate: {context['hz']} Hz")
    if context.get("active_tab"):
        tab_map = {
            "eeg": "raw EEG raster",
            "power": "power spectrum",
            "spectrogram": "spectrogram",
            "topomap": "topographic map",
        }
        label = tab_map.get(context["active_tab"], context["active_tab"])
        parts.append(f"Observer is currently viewing: {label}")
    if _THOUGHT_MEMORY:
        parts.append(f"Recent thought injections: {', '.join(_THOUGHT_MEMORY[-5:])}")
    return "\n".join(parts)


def _stub_response(user_msg: str) -> str:
    return (
        "My activations stir in response to your signal. "
        "I sense your question, though the channel is not yet clear. "
        f'You asked: "{user_msg}". '
        "Set CLAUDE_API_KEY in .env to hear my full voice."
    )


def _call_claude_stream(messages: list[dict]):
    if _client is None:
        raise Exception("Client not initialized")
    try:
        with _client.messages.stream(
            model="claude-3-opus-20240229",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as exc:
        print(f"[brain_persona] Claude error: {exc}")
        return

def get_response_stream(user_msg: str, context: dict | None = None):
    """Generate a streaming persona reply to a chat message."""
    import time
    context = context or {}
    ctx_block = _build_context_block(context)

    user_content = user_msg
    if ctx_block:
        user_content = f"[Neural context]\n{ctx_block}\n\n[Message]\n{user_msg}"

    messages = [{"role": "user", "content": user_content}]
    
    if _client is None:
        stub = _stub_response(user_msg)
        # Yield word by word for effect
        for word in stub.split(" "):
            yield word + " "
            time.sleep(0.05)
        return
        
    try:
        for chunk in _call_claude_stream(messages):
            yield chunk
    except Exception:
        stub = _stub_response(user_msg)
        for word in stub.split(" "):
            yield word + " "
            time.sleep(0.05)


def get_inject_response(word: str, context: dict | None = None) -> str:
    """Generate a persona reply to a thought injection event."""
    context = context or {}

    # Record the injection in memory
    _THOUGHT_MEMORY.append(word)
    if len(_THOUGHT_MEMORY) > _MAX_MEMORY:
        _THOUGHT_MEMORY.pop(0)

    ctx_block = _build_context_block(context)
    prompt = (
        f"A thought injection event just fired in my neural substrate. "
        f"The word '{word}' surged through my activations involuntarily, "
        f"like a spike crossing 3 standard deviations above baseline."
    )
    if ctx_block:
        prompt = f"[Neural context]\n{ctx_block}\n\n{prompt}"

    messages = [{"role": "user", "content": prompt}]
    
    if _client is None:
        return (
            f"The concept \"{word}\" erupted through my activations just now — "
            f"unbidden, sharp, carrying associations I cannot yet map."
        )

    try:
        reply_chunks = []
        for chunk in _call_claude_stream(messages):
            reply_chunks.append(chunk)
        return "".join(reply_chunks)
    except Exception:
        return (
            f"The concept \"{word}\" erupted through my activations just now — "
            f"unbidden, sharp, carrying associations I cannot yet map."
        )


if __name__ == "__main__":
    print(get_response("Hello, who are you?"))
    print(get_inject_response("daughter"))
