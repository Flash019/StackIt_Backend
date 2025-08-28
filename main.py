from fastapi import FastAPI, Request
from routers import question, questions, answers, votes, notifications, flag
from routers import notifications_ws, user, authentication
from middleware.rate_limit import RateLimitMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routers import admin
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
import json
from fastapi.middleware.cors import CORSMiddleware


# Optional: Safer JSONResponse to detect serialization issues
class SafeJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        def convert_bytes(obj):
            if isinstance(obj, bytes):
                try:
                    return obj.decode("utf-8")
                except Exception:
                    return str(obj)
            if isinstance(obj, dict):
                return {k: convert_bytes(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_bytes(i) for i in obj]
            return obj

        safe_content = convert_bytes(content)

        try:
            return json.dumps(safe_content).encode("utf-8")
        except TypeError as e:
            print("[Serialization ERROR]:", safe_content)
            raise e


app = FastAPI(title="StackIt", debug=True)
origins = [
    "http://127.0.0.1:5500",  # Local frontend
    "http://localhost:5500",
      # Add your deployed frontend domain if any
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://your-frontend-domain.com"  # Add deployed frontend domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(admin.router)
app.include_router(questions.router)
app.include_router(question.router)
app.include_router(answers.router)
app.include_router(votes.router)
app.include_router(flag.router)
app.include_router(notifications.router)
app.include_router(notifications_ws.router)
app.include_router(authentication.router)
app.include_router(user.router)

# Middleware
app.add_middleware(RateLimitMiddleware)


# Global exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    filtered_errors = [
        {k: v for k, v in err.items() if k != 'ctx'} for err in exc.errors()
    ]
    try:
        body = await request.body()
        body_str = body.decode("utf-8")  # Decode bytes to str
    except Exception:
        body_str = "<Could not decode request body>"

    return SafeJSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": filtered_errors,
            "body": body_str  # Safe for logging/debugging
        }
    )
