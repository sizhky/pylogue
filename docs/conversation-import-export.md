# Conversation Import/Export

Pylogue supports downloading and reloading chat history as JSON so you can resume a session later.

## Download

Use the download icon in the chat header to save a JSON file.
The file is generated from the in-memory `cards` list and includes the full conversation.

## Upload

Use the upload icon to load a previous JSON file. The UI will rehydrate the conversation and you can keep chatting.

If the responder implements a `load_history(cards)` method, Pylogue will call it after import so the
underlying agent can rebuild its internal memory.

## JSON Formats

Pylogue accepts two JSON shapes:

### Cards (native)

```json
[
  { "id": "0", "question": "hi", "answer": "hello" },
  { "id": "1", "question": "next", "answer": "response" }
]
```

### Role/Content (compatible)

```json
[
  { "role": "User", "content": "hi" },
  { "role": "Assistant", "content": "hello" }
]
```

Role/content messages are paired into cards (User → Assistant). Unpaired messages are ignored.

## Integration Hook

If you want your agent framework to restore context on import, implement:

```python
def load_history(self, cards: list[dict]) -> None:
    ...
```

Pylogue will call this automatically after a successful upload.
