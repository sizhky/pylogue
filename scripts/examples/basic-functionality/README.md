# Pylogue Example Scripts

This folder contains ready-to-run example scripts demonstrating various features of the Pylogue chat framework.

## � Directory Structure

```
scripts/examples/
├── basic-functionality/    # Core framework examples
│   ├── 1-echo-bot.py
│   ├── 2-magic-assistant.py
│   ├── 3-smart-assistant.py
│   ├── 4-code-assistant.py
│   └── 5-supply-chain-rca.py
└── ai/                     # AI integration examples
    └── pydantic-ai.py
```

## �🚀 Quick Start

Each script runs independently on different ports. Simply run:

```bash
# For basic examples
python scripts/examples/basic-functionality/<script-name>.py

# For AI examples
python scripts/examples/ai/<script-name>.py
```

## 📚 Basic Functionality Examples

### 1. Echo Bot (`1-echo-bot.py`)
**Port:** 5001

The simplest possible chat app - echoes back what you say.

```bash
python scripts/examples/basic-functionality/1-echo-bot.py
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
python scripts/examples/basic-functionality/2-magic-assistant.py
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
python scripts/examples/basic-functionality/3-smart-assistant.py
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
python scripts/examples/basic-functionality/4-code-assistant.py
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
python scripts/examples/basic-functionality/5-supply-chain-rca.py
```

**Features:**
- Complete dependency injection
- Custom responder with domain knowledge
- Custom initial messages
- Specialized styling for enterprise use
- Context-aware responses
- Demonstrates full `ChatApp` customization

---

## 🤖 AI Integration Examples

### Pydantic AI (`ai/pydantic-ai.py`)
**Port:** 5002

Integration with Pydantic AI for structured AI responses.

```bash
python scripts/examples/ai/pydantic-ai.py
```

**Features:**
- Pydantic AI integration
- Structured response handling
- Type-safe AI interactions

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