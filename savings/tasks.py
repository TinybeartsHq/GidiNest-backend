# savings/tasks.py
"""
Celery tasks for the savings app.
Handles periodic tasks like unlocking matured savings goals.
"""
from celery import shared_task
from django.utils import timezone
from .models import SavingsGoalModel
import logging

logger = logging.getLogger(__name__)


@shared_task(name='savings.tasks.unlock_matured_goals')
def unlock_matured_goals():
    """
    Periodic task to unlock savings goals that have reached their maturity date.
    Runs daily to check for goals that should be unlocked.
    """
    now = timezone.now()

    # Find all locked goals where maturity date has passed
    matured_goals = SavingsGoalModel.objects.filter(
        is_locked=True,
        maturity_date__lte=now
    )

    unlocked_count = 0
    for goal in matured_goals:
        # Double-check with the model method
        if not goal.is_currently_locked():
            logger.info(f"Unlocking matured goal: {goal.name} (ID: {goal.id}) for user {goal.user.email}")
            # Goal has matured, we can optionally change status or just leave is_locked as True
            # but the is_currently_locked() method will return False
            # Optionally, you could update the goal here if needed
            unlocked_count += 1

    logger.info(f"Checked {matured_goals.count()} goals. {unlocked_count} goals have matured and are now unlocked.")
    return {
        'checked': matured_goals.count(),
        'unlocked': unlocked_count,
        'timestamp': now.isoformat()
    }


@shared_task(name='savings.tasks.calculate_interest_for_goals')
def calculate_interest_for_goals():
    """
    Periodic task to calculate and apply interest to active savings goals.
    This is a placeholder for future interest calculation logic.
    """
    active_goals = SavingsGoalModel.objects.filter(status='active')

    for goal in active_goals:
        # Placeholder: implement your interest calculation logic here
        # For example, daily compound interest, monthly interest, etc.
        # goal.accrued_interest += calculated_interest
        # goal.save(update_fields=['accrued_interest', 'updated_at'])
        pass

    logger.info(f"Interest calculation task ran for {active_goals.count()} active goals")
    return {
        'processed': active_goals.count(),
        'timestamp': timezone.now().isoformat()
    }
