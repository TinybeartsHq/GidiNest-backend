"""
Custom admin views for customer support dashboard
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from account.models import UserModel, CustomerNote, UserSession
from wallet.models import Wallet, WalletTransaction, WithdrawalRequest
from savings.models import SavingsGoalModel
from core.models import ServerLog


@staff_member_required
def support_dashboard(request):
    """
    Custom dashboard view for customer support team showing key metrics and quick actions.
    """
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    # ============================================
    # USER METRICS
    # ============================================
    total_users = UserModel.objects.count()
    active_users = UserModel.objects.filter(is_active=True).count()
    verified_users = UserModel.objects.filter(is_verified=True).count()
    unverified_users = UserModel.objects.filter(is_verified=False).count()
    new_users_24h = UserModel.objects.filter(created_at__gte=last_24h).count()
    new_users_7d = UserModel.objects.filter(created_at__gte=last_7d).count()

    # Users needing attention
    unverified_with_bvn = UserModel.objects.filter(
        is_verified=False,
        has_bvn=True
    ).count()

    # ============================================
    # WALLET & TRANSACTION METRICS
    # ============================================
    total_wallets = Wallet.objects.count()
    total_balance = Wallet.objects.aggregate(total=Sum('balance'))['total'] or 0
    transactions_24h = WalletTransaction.objects.filter(created_at__gte=last_24h).count()

    # Withdrawal metrics
    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').count()
    failed_withdrawals_24h = WithdrawalRequest.objects.filter(
        status='failed',
        created_at__gte=last_24h
    ).count()

    # ============================================
    # SAVINGS METRICS
    # ============================================
    active_savings_goals = SavingsGoalModel.objects.filter(status='active').count()
    total_savings = SavingsGoalModel.objects.filter(
        status='active'
    ).aggregate(total=Sum('current_amount'))['total'] or 0

    # ============================================
    # SUPPORT METRICS
    # ============================================
    # Customer notes
    open_notes = CustomerNote.objects.filter(status='open').count()
    in_progress_notes = CustomerNote.objects.filter(status='in_progress').count()
    flagged_notes = CustomerNote.objects.filter(flagged=True, status__in=['open', 'in_progress']).count()
    urgent_notes = CustomerNote.objects.filter(
        priority='urgent',
        status__in=['open', 'in_progress']
    ).count()
    notes_created_24h = CustomerNote.objects.filter(created_at__gte=last_24h).count()
    notes_resolved_24h = CustomerNote.objects.filter(
        status__in=['resolved', 'closed'],
        resolved_at__gte=last_24h
    ).count()

    # Notes by category (top 5)
    notes_by_category = CustomerNote.objects.filter(
        status__in=['open', 'in_progress']
    ).values('category').annotate(count=Count('id')).order_by('-count')[:5]

    # ============================================
    # SECURITY METRICS
    # ============================================
    active_sessions = UserSession.objects.filter(is_active=True).count()
    new_sessions_24h = UserSession.objects.filter(created_at__gte=last_24h).count()

    # ============================================
    # SYSTEM HEALTH
    # ============================================
    errors_24h = ServerLog.objects.filter(
        level__in=['ERROR', 'CRITICAL'],
        timestamp__gte=last_24h
    ).count()

    # Recent errors grouped by path
    recent_error_paths = ServerLog.objects.filter(
        level__in=['ERROR', 'CRITICAL'],
        timestamp__gte=last_24h
    ).values('request_path').annotate(count=Count('id')).order_by('-count')[:5]

    # ============================================
    # RECENT ACTIVITY
    # ============================================
    # Recent support notes
    recent_notes = CustomerNote.objects.select_related('user', 'created_by').order_by('-created_at')[:10]

    # Recent users needing verification
    recent_unverified = UserModel.objects.filter(
        is_verified=False,
        has_bvn=True
    ).order_by('-created_at')[:10]

    # Recent failed withdrawals
    recent_failed_withdrawals = WithdrawalRequest.objects.filter(
        status='failed'
    ).select_related('user').order_by('-created_at')[:10]

    # ============================================
    # ALERTS & WARNINGS
    # ============================================
    alerts = []

    if urgent_notes > 0:
        alerts.append({
            'type': 'danger',
            'message': f'{urgent_notes} urgent customer note(s) need immediate attention',
            'link': '/admin/account/customernote/?priority__exact=urgent&status__in=open,in_progress'
        })

    if flagged_notes > 0:
        alerts.append({
            'type': 'warning',
            'message': f'{flagged_notes} flagged customer note(s) need review',
            'link': '/admin/account/customernote/?flagged__exact=1&status__in=open,in_progress'
        })

    if pending_withdrawals > 10:
        alerts.append({
            'type': 'warning',
            'message': f'{pending_withdrawals} withdrawal requests are pending',
            'link': '/admin/wallet/withdrawalrequest/?status__exact=pending'
        })

    if failed_withdrawals_24h > 5:
        alerts.append({
            'type': 'warning',
            'message': f'{failed_withdrawals_24h} withdrawals failed in the last 24 hours',
            'link': '/admin/wallet/withdrawalrequest/?status__exact=failed'
        })

    if errors_24h > 50:
        alerts.append({
            'type': 'danger',
            'message': f'{errors_24h} errors logged in the last 24 hours - system may need attention',
            'link': '/admin/core/serverlog/?level__in=ERROR,CRITICAL'
        })

    if unverified_with_bvn > 20:
        alerts.append({
            'type': 'info',
            'message': f'{unverified_with_bvn} users with BVN waiting for verification',
            'link': '/admin/account/usermodel/?is_verified__exact=0&has_bvn__exact=1'
        })

    # ============================================
    # QUICK STATS FOR CARDS
    # ============================================
    context = {
        'title': 'Customer Support Dashboard',

        # User metrics
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
        'new_users_24h': new_users_24h,
        'new_users_7d': new_users_7d,
        'unverified_with_bvn': unverified_with_bvn,

        # Wallet metrics
        'total_wallets': total_wallets,
        'total_balance': total_balance / 100,  # Convert from kobo to naira
        'transactions_24h': transactions_24h,
        'pending_withdrawals': pending_withdrawals,
        'failed_withdrawals_24h': failed_withdrawals_24h,

        # Savings metrics
        'active_savings_goals': active_savings_goals,
        'total_savings': total_savings / 100,  # Convert from kobo to naira

        # Support metrics
        'open_notes': open_notes,
        'in_progress_notes': in_progress_notes,
        'flagged_notes': flagged_notes,
        'urgent_notes': urgent_notes,
        'notes_created_24h': notes_created_24h,
        'notes_resolved_24h': notes_resolved_24h,
        'notes_by_category': notes_by_category,

        # Security metrics
        'active_sessions': active_sessions,
        'new_sessions_24h': new_sessions_24h,

        # System health
        'errors_24h': errors_24h,
        'recent_error_paths': recent_error_paths,

        # Recent activity
        'recent_notes': recent_notes,
        'recent_unverified': recent_unverified,
        'recent_failed_withdrawals': recent_failed_withdrawals,

        # Alerts
        'alerts': alerts,
    }

    return render(request, 'admin/support_dashboard.html', context)
