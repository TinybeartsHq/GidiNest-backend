# savings/serializers.py
from rest_framework import serializers
from .models import SavingsGoalModel, SavingsGoalTransaction


class SavingsGoalSerializer(serializers.ModelSerializer):
    """
    Serializer for the SavingsGoal model.
    Handles serialization and deserialization of savings goal data.
    """
    # Make 'amount' optional for creation if you want it to default to 0
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False, # Make current amount optional for creation
        min_value=0.00 # Ensure amount is not negative
    )
    target_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01 # Ensure target amount is positive
    )
    status = serializers.ChoiceField(
        choices=SavingsGoalModel.STATUS_CHOICES,
        required=False # Allow status to be defaulted in model
    )

    class Meta:
        model = SavingsGoalModel
        fields = ['id', 'name', 'amount', 'target_amount','interest_rate','accrued_interest', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'interest_rate', 'created_at', 'updated_at'] # These fields are set by the system

    def validate(self, data):
        """
        Check that the target amount is greater than or equal to the current amount.
        """
        current_amount = data.get('amount', self.instance.amount if self.instance else 0)
        target_amount = data.get('target_amount', self.instance.target_amount if self.instance else None)

        if target_amount is not None and current_amount > target_amount:
            raise serializers.ValidationError("Current amount cannot be greater than the target amount.")
        return data
    


class SavingsGoalTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for SavingsGoalTransaction model to display history for a specific goal.
    """
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    goal_name = serializers.CharField(source='goal.name', read_only=True) # To show goal name

    class Meta:
        model = SavingsGoalTransaction
        fields = [
            'id', 'goal', 'goal_name', 'transaction_type', 'transaction_type_display',
            'amount', 'description', 'goal_current_amount', 'timestamp'
        ]
        read_only_fields = fields  
        depth = 1