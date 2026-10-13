from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    def __init__(self, status_code, code, message, *, extra=None, headers=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.extra = extra or {}
        self.headers = headers


async def api_error_handler(request: Request, error: APIError):
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                **error.extra,
            }
        },
        headers=error.headers,
    )


async def request_validation_handler(request: Request, error: RequestValidationError):
    malformed_json = any(
        issue.get("type") == "json_invalid" for issue in error.errors()
    )
    return JSONResponse(
        status_code=400 if malformed_json else 422,
        content={
            "error": {
                "code": "invalid_json" if malformed_json else "invalid_request",
                "message": "The request body is malformed."
                if malformed_json
                else "The request fields are invalid.",
            }
        },
    )


async def http_error_handler(request: Request, error: StarletteHTTPException):
    status = error.status_code
    code, message = {
        404: ("not_found", "The requested resource was not found."),
        405: ("method_not_allowed", "The request method is not allowed."),
    }.get(status, ("request_failed", "The request could not be completed."))
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


async def internal_error_handler(request: Request, error: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "The request could not be completed.",
            }
        },
    )
