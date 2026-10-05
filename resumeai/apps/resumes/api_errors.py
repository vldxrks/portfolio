from rest_framework.views import exception_handler as drf_handler


def exception_handler(exc, context):
    """Unified error format: {"error": {"code", "message", "details"}} - no stack traces."""
    response = drf_handler(exc, context)
    if response is None:
        return None
    detail = response.data
    code = getattr(getattr(exc, "default_code", None), "upper", lambda: "ERROR")().upper()
    message = detail.get("detail") if isinstance(detail, dict) and "detail" in detail else "Request failed."
    details = {} if isinstance(detail, dict) and "detail" in detail else detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:  # already shaped
        response.data = {"error": detail}
        return response
    response.data = {"error": {"code": code, "message": str(message), "details": details}}
    return response
