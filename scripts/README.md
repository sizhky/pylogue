# Pylogue Example Scripts

This folder contains ready-to-run example scripts demonstrating various features of the Pylogue chat framework.

## 🚀 Quick Start

Each script runs independently on different ports. Simply run:

```bash
python scripts/<script-name>.py
```

## 📚 Examples

### 1. Echo Bot (`1-echo-bot.py`)
**Port:** 5001

The simplest possible chat app - echoes back what you say.

```bash
python scripts/1-echo-bot.py
```

**Features:**
- Minimal setup (5 lines of code)
- Default styling
- Basic async responder

---

### 2. Magic Assistant (`2-magic-assistant.py`)
**Port:** 5001

Custom styled chat with mystical theme.

```bash
python scripts/2-magic-assistant.py
```

**Features:**
- Custom colors and emojis
- Randomized responses
- Custom app title and styling
- Demonstrates `ChatCard` and `ChatAppConfig` customization

---

### 3. Smart Assistant (`3-smart-assistant.py`)
**Port:** 5001

Context-aware assistant that uses conversation history.

```bash
python scripts/3-smart-assistant.py
```

**Features:**
- Conversation history tracking
- Keyword detection
- Message count display
- Context provider integration
- Demonstrates how to build stateful conversations

---

### 4. Code Assistant (`4-code-assistant.py`)
**Port:** 5001

Multi-language code examples with syntax highlighting.

```bash
python scripts/4-code-assistant.py
```

**Features:**
- Python and JavaScript code examples
- Syntax highlighting enabled
- Code block rendering with markdown
- Developer-themed styling

---

### 5. Supply Chain RCA (`5-supply-chain-rca.py`)
**Port:** 5001

Full custom DI implementation for supply chain analysis.

```bash
python scripts/5-supply-chain-rca.py
```

**Features:**
- Complete dependency injection
- Custom responder with domain knowledge
- Custom initial messages
- Specialized styling for enterprise use
- Context-aware responses
- Demonstrates full `ChatApp` customization

---

## 🔧 Customization

Each script demonstrates different aspects of Pylogue:

| Script | Demonstrates |
|--------|--------------|
| `1-echo-bot.py` | Minimal setup with `create_default_chat_app()` |
| `2-magic-assistant.py` | Custom styling via `ChatCard` and `ChatAppConfig` |
| `3-smart-assistant.py` | Context providers and stateful conversations |
| `4-code-assistant.py` | Markdown rendering and syntax highlighting |
| `5-supply-chain-rca.py` | Full DI with custom components |

---