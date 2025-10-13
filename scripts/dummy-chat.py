from pylogue.chatapp import create_default_chat_app


async def my_responder(msg: str, context=None) -> str:
    return f"You said: {msg}"


app = create_default_chat_app(responder=my_responder)
app.run(port=5001)
