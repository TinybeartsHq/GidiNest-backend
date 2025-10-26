from django.contrib import admin
from .models import SavingsGoalModel, SavingsGoalTransaction


@admin.register(SavingsGoalModel)
class SavingsGoalModelAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'name',
        'target_amount',
        'amount',
        'accrued_interest',
        'interest_rate',
        'status',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'name')
    readonly_fields = ('created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(SavingsGoalTransaction)
class SavingsGoalTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'goal_name',
        'user_email',
        'transaction_type',
        'amount',
        'goal_current_amount',
        'timestamp',
    )
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('goal__name', 'goal__user__email', 'description')
    readonly_fields = ('timestamp',)

    def goal_name(self, obj):
        return obj.goal.name
    goal_name.short_description = 'Goal Name'

    def user_email(self, obj):
        return obj.goal.user.email
    user_email.short_description = 'User Email'
