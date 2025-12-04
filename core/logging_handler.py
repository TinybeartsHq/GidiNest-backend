import logging
from django.utils import timezone


class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that saves logs to the database.
    """

    def emit(self, record):
        """
        Save the log record to the database.
        """
        try:
            # Import here to avoid circular imports
            from core.models import ServerLog

            # Extract exception info if available
            exception_text = None
            if record.exc_info:
                exception_text = self.format(record)

            # Extract request info if available
            request_path = None
            request_method = None
            user_email = None
            ip_address = None

            if hasattr(record, 'request'):
                request = record.request
                request_path = getattr(request, 'path', None)
                request_method = getattr(request, 'method', None)

                # Get user info if authenticated
                if hasattr(request, 'user') and request.user.is_authenticated:
                    user_email = getattr(request.user, 'email', None)

                # Get IP address - only if META attribute exists (not a socket object)
                if hasattr(request, 'META'):
                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    if x_forwarded_for:
                        ip_address = x_forwarded_for.split(',')[0]
                    else:
                        ip_address = request.META.get('REMOTE_ADDR')

            # Create log entry
            ServerLog.objects.create(
                level=record.levelname,
                logger_name=record.name,
                message=record.getMessage(),
                pathname=record.pathname,
                function_name=record.funcName,
                line_number=record.lineno,
                exception=exception_text,
                request_path=request_path,
                request_method=request_method,
                user_email=user_email,
                ip_address=ip_address,
                timestamp=timezone.now()
            )
        except Exception as e:
            # Don't let logging errors break the application
            # Fall back to printing to stderr
            import sys
            print(f"Error saving log to database: {e}", file=sys.stderr)
