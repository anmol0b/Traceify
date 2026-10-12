from __future__ import annotations


class TraceifyError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidHandle(TraceifyError):
    status_code = 422
    code = "invalid_handle"


class ProfileNotFound(TraceifyError):
    status_code = 404
    code = "not_found"


class PrivateAccount(TraceifyError):
    status_code = 403
    code = "private_account"


class UpstreamRateLimit(TraceifyError):
    status_code = 429
    code = "upstream_rate_limited"


class RateLimited(TraceifyError):
    status_code = 429
    code = "rate_limited"


class UpstreamError(TraceifyError):
    status_code = 502
    code = "upstream_error"


class NotConfigured(TraceifyError):
    status_code = 503
    code = "not_configured"
