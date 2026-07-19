from fastapi import FastAPI

app = FastAPI(title="RAG Assistant Lab")

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "RAG Assistant Lab API is running"
    }