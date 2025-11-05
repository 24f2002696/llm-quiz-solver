from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from quiz_solver import QuizSolver
import asyncio

load_dotenv()

app = FastAPI(title="LLM Quiz Solver", version="1.0")

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

@app.post("/solve")
async def solve_quiz(request: QuizRequest):
    """Endpoint to receive and solve quiz tasks"""
    
    # Verify secret
    expected_secret = os.getenv("SECRET_STRING")
    if request.secret != expected_secret:
        print(f"Secret mismatch: got '{request.secret}', expected '{expected_secret}'")
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Verify email
    expected_email = os.getenv("STUDENT_EMAIL")
    if request.email != expected_email:
        print(f"Email mismatch: got '{request.email}', expected '{expected_email}'")
        raise HTTPException(status_code=403, detail="Invalid email")
    
    print(f"\n{'='*60}")
    print(f"Received quiz request:")
    print(f"Email: {request.email}")
    print(f"URL: {request.url}")
    print(f"{'='*60}\n")
    
    # Solve the quiz
    solver = QuizSolver()
    try:
        result = await solver.solve_quiz_chain(request.url)
        return {
            "status": "success", 
            "message": "Quiz solving completed", 
            "result": result
        }
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    return {
        "message": "LLM Quiz Solver API is running",
        "status": "ok",
        "email": os.getenv("STUDENT_EMAIL"),
        "endpoints": {
            "POST /solve": "Submit quiz URL to solve",
            "GET /health": "Check API health"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "llm-quiz-solver"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)