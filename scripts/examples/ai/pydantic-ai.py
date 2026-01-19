# fasthtml solveit
if __name__ == "__main__":
    print("✅ Pydantic AI Chat ready!")
    print("💬 Try asking questions and watch responses stream in real-time!")
    print("🔗 Chat endpoint: http://localhost:5001/")
    import uvicorn
    uvicorn.run(
        "scripts.examples.ai.pydantic_ai_app:app_factory",
        host="0.0.0.0",
        port=5002,
        reload=True,
        factory=True,
    )
