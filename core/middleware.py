import json
import logging

from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Financial endpoints that support Idempotency-Key
IDEMPOTENT_PATHS = [
    '/api/v2/wallet/9psb/debit',
    '/api/v2/wallet/9psb/credit',
    '/api/v2/wallet/9psb/transfer/banks',
    '/api/v2/wallet/withdraw',
    '/api/v1/wallet/withdraw/request',
]

CACHE_TTL = 3600  # 1 hour


class IdempotencyKeyMiddleware:
    """
    Middleware that caches successful responses for financial POST endpoints
    when an Idempotency-Key header is provided.

    - Backward-compatible: requests without the header are unaffected.
    - Cache key is scoped per authenticated user to prevent cross-user collisions.
    - Only 2xx responses are cached; errors are never cached so the client can retry.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only intercept POST requests to financial endpoints
        if request.method != 'POST':
            return self.get_response(request)

        # Check if path matches any idempotent endpoint
        path = request.path.rstrip('/')
        if not any(path == p.rstrip('/') for p in IDEMPOTENT_PATHS):
            return self.get_response(request)

        # No header → proceed normally (backward-compatible)
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return self.get_response(request)

        # Build user-scoped cache key (user_id available after AuthenticationMiddleware)
        user_id = getattr(request.user, 'id', 'anon') if hasattr(request, 'user') else 'anon'
        cache_key = f'idempotency:{user_id}:{idempotency_key}'

        # Check cache for previous response
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Idempotency cache hit: key={idempotency_key}, user={user_id}")
            return JsonResponse(
                cached['body'],
                status=cached['status'],
                safe=False,
            )

        # Process the request
        response = self.get_response(request)

        # Cache only successful (2xx) responses
        if 200 <= response.status_code < 300:
            try:
                body = json.loads(response.content)
                cache.set(cache_key, {
                    'status': response.status_code,
                    'body': body,
                }, CACHE_TTL)
            except (json.JSONDecodeError, TypeError):
                pass  # Non-JSON response, skip caching

        return response
