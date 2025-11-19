# Server Logs Administration Guide

## Overview

The GidiNest backend now includes a comprehensive server logging system that captures and stores application logs in the database for easy monitoring and debugging through the Django admin panel.

## Features

- **Real-time log capture** - All application logs are automatically saved to the database
- **Color-coded log levels** - Easy visual distinction between DEBUG, INFO, WARNING, ERROR, and CRITICAL logs
- **Rich filtering** - Filter by log level, logger name, timestamp, and request method
- **Request tracking** - Logs include HTTP request path, method, user email, and IP address
- **Exception capture** - Full exception tracebacks are stored for ERROR and CRITICAL logs
- **Source code tracking** - File path, function name, and line number where log originated
- **Statistics dashboard** - View log counts, recent errors, and trends
- **Search functionality** - Full-text search across log messages, exceptions, and metadata

## Accessing Server Logs

1. Navigate to the Django admin panel at: `https://app.gidinest.com/internal-admin/`
2. Log in with your superuser credentials
3. Click on **"Server Logs"** in the Core section

## Log Levels

Logs are captured at different severity levels:

- **DEBUG** (Gray) - Detailed diagnostic information
- **INFO** (Blue) - General informational messages
- **WARNING** (Orange) - Warning messages about potential issues
- **ERROR** (Red) - Error messages for serious problems
- **CRITICAL** (Dark Red) - Critical errors that may cause system failure

## Filtering Logs

Use the right sidebar filters to narrow down logs:

- **By Level** - Filter by DEBUG, INFO, WARNING, ERROR, or CRITICAL
- **By Logger Name** - Filter by Django components (django.request, django.server) or apps (account, wallet, savings, etc.)
- **By Date** - Filter logs by today, past 7 days, this month, or custom date range
- **By Request Method** - Filter by HTTP method (GET, POST, PUT, DELETE, etc.)

## Search Functionality

Use the search bar to find logs containing specific:
- Log messages
- Logger names
- User emails
- Request paths
- Exception text
- IP addresses

## Viewing Log Details

Click on any log entry to view full details:

1. **Log Information** - Timestamp, level, logger name, and full message
2. **Source Location** - File path, function name, and line number
3. **Request Information** - Request path, method, user, and IP address
4. **Exception Details** - Full exception traceback (if applicable)

## Statistics Dashboard

At the top of the Server Logs page, you'll see:
- **Total Logs** - All logs in the database
- **Logs Last Hour** - Recent activity indicator
- **Logs Last 24 Hours** - Daily activity
- **Recent Errors** - ERROR and CRITICAL logs in last 24 hours
- **Level Breakdown** - Count of each log level in last 24 hours

## Logging in Your Code

To add custom logging in your Django apps:

```python
import logging

# Create logger for your module
logger = logging.getLogger(__name__)

# Log at different levels
logger.debug("Detailed debugging information")
logger.info("General information message")
logger.warning("Warning message about potential issue")
logger.error("Error occurred", exc_info=True)  # Include exception
logger.critical("Critical system error")
```

### Example in Views

```python
import logging
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class MyAPIView(APIView):
    def post(self, request):
        try:
            logger.info(f"User {request.user.email} initiated action")
            # Your code here
            return Response({"success": True})
        except Exception as e:
            logger.error(f"Error in MyAPIView: {str(e)}", exc_info=True)
            return Response({"error": "Internal error"}, status=500)
```

## Cleaning Up Old Logs

To prevent database bloat, regularly clean up old logs using the management command:

```bash
# Delete logs older than 30 days (default)
python manage.py cleanup_logs

# Delete logs older than 7 days
python manage.py cleanup_logs --days 7

# Dry run (see what would be deleted without actually deleting)
python manage.py cleanup_logs --days 30 --dry-run
```

### Automated Cleanup with Cron

Add to your crontab for automatic weekly cleanup:

```bash
# Clean up logs older than 30 days every Sunday at 2 AM
0 2 * * 0 cd /path/to/gidinest_backend && source venv/bin/activate && python manage.py cleanup_logs --days 30
```

### Automated Cleanup with Celery Beat

Alternatively, create a periodic task in Django admin (django-celery-beat):

1. Go to **Periodic Tasks** in admin
2. Create new periodic task
3. Name: "Cleanup Old Server Logs"
4. Task: `core.tasks.cleanup_old_logs` (you'll need to create this task)
5. Schedule: Every 7 days

## Current Logging Configuration

The following Django components and apps are configured to log to the database:

- **django** - Core Django framework logs
- **django.request** - HTTP request errors (4xx, 5xx)
- **django.server** - Development server logs
- **account** - User account operations
- **wallet** - Wallet transactions and operations
- **savings** - Savings goals operations
- **onboarding** - User onboarding process
- **community** - Community posts and interactions
- **providers** - External provider integrations

## Performance Considerations

- Logs are written asynchronously to minimize impact on request handling
- Only INFO level and above logs are saved to database (DEBUG logs only go to console)
- Database has indexes on `timestamp`, `level`, `logger_name`, `request_path`, and `user_email` for fast queries
- Regular cleanup of old logs is recommended to maintain performance

## Troubleshooting

### Logs not appearing in admin

1. Check that migrations have been applied: `python manage.py migrate core`
2. Verify logging configuration in `settings.py`
3. Check that `core.logging_handler.DatabaseLogHandler` is in LOGGING handlers
4. Ensure the app generating logs is listed in LOGGING loggers

### Database growing too large

- Run the cleanup command regularly: `python manage.py cleanup_logs --days 7`
- Consider reducing log retention period
- Review which loggers are enabled and their log levels

### Performance issues

- Increase cleanup frequency
- Add database indexes if needed
- Consider using separate database for logs
- Reduce log level from INFO to WARNING for high-traffic apps

## Security Notes

- Server logs are only accessible to superusers in the admin panel
- Logs may contain sensitive information (user emails, IP addresses, request paths)
- Regular cleanup helps maintain GDPR compliance
- Consider log rotation policies based on your data retention requirements

## Support

For issues or questions about the logging system, contact the backend development team.
