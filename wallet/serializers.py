from rest_framework import serializers

from wallet.models import Wallet,WalletTransaction


class WalletBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying the wallet balance.
    """
    class Meta:
        model = Wallet
        fields = ['balance', 'currency','account_number','bank','bank_code','account_name']
        read_only_fields = ['balance', 'currency','account_number','bank','bank_code','account_name']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for WalletTransaction model.
    """

    wallet_account_number = serializers.CharField(source='wallet.account_number')

    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet_account_number', 'transaction_type', 'amount', 'description', 
            'sender_name', 'sender_account', 'created_at', 'updated_at'
        ]
