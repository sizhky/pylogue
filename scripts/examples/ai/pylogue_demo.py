# fasthtml solveit
if __name__ == "__main__":
    print("✅ Pydantic AI Chat ready!")
    print("💬 Try asking questions and watch responses stream in real-time!")
    print("🔗 Chat endpoint: http://localhost:5003/")
    import uvicorn
    uvicorn.run(
        "scripts.examples.ai.pylogue_demo_app:app_factory",
        host="0.0.0.0",
        port=5003,
        reload=True,
        factory=True,
    )
