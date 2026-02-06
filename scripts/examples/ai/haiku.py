# fasthtml solveit
if __name__ == "__main__":
    print("✅ Haiku bot ready!")
    print("💬 Replies are streamed in 5-7-5 format.")
    print("🔗 Chat endpoint: http://localhost:5004/")

    import uvicorn

    uvicorn.run(
        "scripts.examples.ai.haiku_app:app_factory",
        host="0.0.0.0",
        port=5004,
        reload=True,
        factory=True,
    )
