# transactions/views.py
"""
Transaction Views for Mobile App V2 API
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Q
from django.core.paginator import Paginator, EmptyPage
from decimal import Decimal
from datetime import datetime

from wallet.models import WalletTransaction, WithdrawalRequest
from savings.models import SavingsGoalTransaction


class TransactionListView(APIView):
    """
    Comprehensive Transaction List API
    Supports filtering by type, status, date range

    GET /api/v2/transactions/

    Query Params:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - type: Transaction type filter (credit, debit, contribution, withdrawal)
    - status: Status filter (pending, processing, completed, failed)
    - start_date: Start date (ISO format: 2025-11-01)
    - end_date: End date (ISO format: 2025-11-30)

    Returns:
    - Paginated transaction list
    - Summary statistics
    - Filters applied
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get query parameters
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        txn_type = request.query_params.get('type', None)
        txn_status = request.query_params.get('status', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        # Collect all transactions
        all_transactions = []

        # Get wallet transactions
        try:
            wallet = user.wallet
            wallet_txns = WalletTransaction.objects.filter(wallet=wallet)

            # Apply filters
            if txn_type and txn_type in ['credit', 'debit']:
                wallet_txns = wallet_txns.filter(transaction_type=txn_type)

            if start_date:
                wallet_txns = wallet_txns.filter(created_at__gte=start_date)

            if end_date:
                wallet_txns = wallet_txns.filter(created_at__lte=end_date)

            # Convert to common format
            for txn in wallet_txns:
                all_transactions.append({
                    "id": str(txn.id),
                    "type": txn.transaction_type,
                    "amount": str(txn.amount),
                    "fee": str(txn.total_fee),
                    "net_amount": str(txn.net_amount or txn.amount),
                    "description": txn.description or "Wallet transaction",
                    "status": txn.status or "completed",
                    "created_at": txn.created_at.isoformat(),
                    "metadata": {
                        "sender_name": txn.sender_name,
                        "sender_account": txn.sender_account,
                        "external_reference": txn.external_reference
                    },
                    "source": "wallet"
                })
        except ObjectDoesNotExist:
            pass  # No wallet yet

        # Get savings goal transactions
        goal_txns = SavingsGoalTransaction.objects.filter(
            goal__user=user
        )

        # Apply filters
        if txn_type and txn_type in ['contribution', 'withdrawal']:
            goal_txns = goal_txns.filter(transaction_type=txn_type)

        if start_date:
            goal_txns = goal_txns.filter(timestamp__gte=start_date)

        if end_date:
            goal_txns = goal_txns.filter(timestamp__lte=end_date)

        # Convert to common format
        for txn in goal_txns:
            all_transactions.append({
                "id": str(txn.id),
                "type": txn.transaction_type,
                "amount": str(txn.amount),
                "description": txn.description or f"Goal: {txn.goal.name}",
                "status": "completed",  # Goal transactions are always completed
                "created_at": txn.timestamp.isoformat(),
                "metadata": {
                    "goal_name": txn.goal.name,
                    "goal_current_amount": str(txn.goal_current_amount)
                },
                "source": "savings_goal"
            })

        # Sort by date (most recent first)
        all_transactions.sort(key=lambda x: x['created_at'], reverse=True)

        # Calculate summary before pagination
        summary = self._calculate_summary(all_transactions, user)

        # Paginate
        paginator = Paginator(all_transactions, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return Response({
            "success": True,
            "data": {
                "transactions": list(page_obj),
                "pagination": {
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total": paginator.count,
                    "total_pages": paginator.num_pages,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous()
                },
                "summary": summary,
                "filters_applied": {
                    "type": txn_type,
                    "status": txn_status,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }, status=status.HTTP_200_OK)

    def _calculate_summary(self, transactions, user):
        """Calculate summary statistics"""
        total_deposits = Decimal('0.00')
        total_withdrawals = Decimal('0.00')
        total_contributions = Decimal('0.00')
        total_goal_withdrawals = Decimal('0.00')

        for txn in transactions:
            amount = Decimal(txn['amount'])
            if txn['type'] == 'credit':
                total_deposits += amount
            elif txn['type'] == 'debit':
                total_withdrawals += amount
            elif txn['type'] == 'contribution':
                total_contributions += amount
            elif txn['type'] == 'withdrawal':
                total_goal_withdrawals += amount

        return {
            "total_deposits": str(total_deposits),
            "total_withdrawals": str(total_withdrawals),
            "total_contributions": str(total_contributions),
            "total_goal_withdrawals": str(total_goal_withdrawals),
            "net_change": str(total_deposits - total_withdrawals)
        }


class TransactionDetailView(APIView):
    """
    Detailed Transaction View
    Returns all transaction information including metadata

    GET /api/v2/transactions/<id>/

    Returns:
    - Complete transaction details
    - Timeline (if available)
    - Related withdrawal request info (if applicable)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, transaction_id):
        user = request.user

        # Try to find the transaction in wallet transactions
        try:
            wallet = user.wallet
            wallet_txn = WalletTransaction.objects.get(id=transaction_id, wallet=wallet)

            # Check if this is related to a withdrawal request
            withdrawal_info = None
            try:
                withdrawal = WithdrawalRequest.objects.get(
                    user=user,
                    transaction_ref=wallet_txn.external_reference
                )
                withdrawal_info = {
                    "bank_name": withdrawal.bank_name,
                    "bank_code": withdrawal.bank_code,
                    "account_number": withdrawal.account_number,
                    "account_name": withdrawal.bank_account_name,
                    "status": withdrawal.status,
                    "transaction_ref": withdrawal.transaction_ref,
                    "error_message": withdrawal.error_message,
                    "timeline": self._build_withdrawal_timeline(withdrawal)
                }
            except WithdrawalRequest.DoesNotExist:
                pass

            return Response({
                "success": True,
                "data": {
                    "id": str(wallet_txn.id),
                    "type": wallet_txn.transaction_type,
                    "amount": str(wallet_txn.amount),
                    "fee": str(wallet_txn.total_fee),
                    "fee_breakdown": {
                        "transfer_fee": str(wallet_txn.fee_amount),
                        "vat": str(wallet_txn.vat_amount),
                        "emtl": str(wallet_txn.emtl_amount),
                        "commission": str(wallet_txn.commission_amount),
                    },
                    "net_amount": str(wallet_txn.net_amount or wallet_txn.amount),
                    "description": wallet_txn.description or "Wallet transaction",
                    "status": wallet_txn.status or "completed",
                    "created_at": wallet_txn.created_at.isoformat(),
                    "metadata": {
                        "sender_name": wallet_txn.sender_name,
                        "sender_account": wallet_txn.sender_account,
                        "external_reference": wallet_txn.external_reference
                    },
                    "withdrawal_info": withdrawal_info,
                    "source": "wallet"
                }
            }, status=status.HTTP_200_OK)

        except WalletTransaction.DoesNotExist:
            pass
        except ObjectDoesNotExist:
            pass

        # Try to find in goal transactions
        try:
            goal_txn = SavingsGoalTransaction.objects.get(
                id=transaction_id,
                goal__user=user
            )

            return Response({
                "success": True,
                "data": {
                    "id": str(goal_txn.id),
                    "type": goal_txn.transaction_type,
                    "amount": str(goal_txn.amount),
                    "fee": "0.00",
                    "net_amount": str(goal_txn.amount),
                    "description": goal_txn.description or f"Goal: {goal_txn.goal.name}",
                    "status": "completed",
                    "created_at": goal_txn.timestamp.isoformat(),
                    "metadata": {
                        "goal_id": str(goal_txn.goal.id),
                        "goal_name": goal_txn.goal.name,
                        "goal_target": str(goal_txn.goal.target_amount),
                        "goal_current_amount": str(goal_txn.goal_current_amount),
                        "goal_status": goal_txn.goal.status
                    },
                    "source": "savings_goal"
                }
            }, status=status.HTTP_200_OK)

        except SavingsGoalTransaction.DoesNotExist:
            pass

        # Transaction not found
        return Response({
            "success": False,
            "message": "Transaction not found",
            "detail": "The requested transaction does not exist or you don't have permission to view it."
        }, status=status.HTTP_404_NOT_FOUND)

    def _build_withdrawal_timeline(self, withdrawal):
        """Build timeline for withdrawal request"""
        timeline = [
            {
                "status": "initiated",
                "timestamp": withdrawal.created_at.isoformat(),
                "note": "Withdrawal request received"
            }
        ]

        if withdrawal.status in ['processing', 'completed', 'failed']:
            timeline.append({
                "status": "processing",
                "timestamp": withdrawal.created_at.isoformat(),
                "note": "Processing via payment provider"
            })

        if withdrawal.status == 'completed':
            timeline.append({
                "status": "completed",
                "timestamp": withdrawal.updated_at.isoformat(),
                "note": "Transfer successful"
            })
        elif withdrawal.status == 'failed':
            timeline.append({
                "status": "failed",
                "timestamp": withdrawal.updated_at.isoformat(),
                "note": withdrawal.error_message or "Transfer failed"
            })

        return timeline
