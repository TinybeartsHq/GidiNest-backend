# wallet/fee_utils.py
"""
Centralized fee calculation for all wallet transactions.
All functions return Decimal values rounded to 2 decimal places.
"""
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

TWO_PLACES = Decimal('0.01')


@dataclass
class TransferFeeBreakdown:
    """Fee breakdown for transfers, withdrawals, and deposits (EMTL-only for deposits)."""
    gross_amount: Decimal
    transfer_fee: Decimal
    vat: Decimal
    emtl: Decimal
    total_fees: Decimal
    net_amount: Decimal


@dataclass
class GiftFeeBreakdown:
    """Fee breakdown for baby fund gifts — flat 1.5% fee."""
    gross_amount: Decimal
    gift_fee: Decimal
    total_fees: Decimal
    net_amount: Decimal


@dataclass
class DisbursementFeeBreakdown:
    """Fee breakdown for fund withdrawals — flat 1% fee."""
    gross_amount: Decimal
    disbursement_fee: Decimal
    total_fees: Decimal
    net_amount: Decimal


@dataclass
class PaymentLinkFeeBreakdown:
    """Fee breakdown for payment link contributions."""
    gross_amount: Decimal
    commission: Decimal
    vat_on_commission: Decimal
    total_fees: Decimal
    net_amount: Decimal


def _round(value: Decimal) -> Decimal:
    """Round to 2 decimal places using banker's rounding."""
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_transfer_fees(amount, config=None) -> TransferFeeBreakdown:
    """
    Calculate all fees for a transfer/withdrawal/deposit.

    Fee structure:
    - Transfer fee: tiered by amount
    - VAT: 7.5% of transfer fee (NOT of principal)
    - EMTL/Stamp Duty: ₦50 if amount >= ₦10,000

    Args:
        amount: The gross (original) transaction amount
        config: Optional FeeConfiguration instance (fetched if not provided)

    Returns:
        TransferFeeBreakdown dataclass
    """
    if config is None:
        from wallet.models import FeeConfiguration
        config = FeeConfiguration.get_active()

    amount = Decimal(str(amount))

    # Determine tiered transfer fee
    if amount <= config.transfer_fee_tier1_max:
        transfer_fee = config.transfer_fee_tier1_amount
    elif amount <= config.transfer_fee_tier2_max:
        transfer_fee = config.transfer_fee_tier2_amount
    else:
        transfer_fee = config.transfer_fee_tier3_amount

    # VAT on transfer fee (NOT on principal)
    vat = _round(transfer_fee * config.vat_rate)

    # EMTL / Stamp Duty
    emtl = config.emtl_amount if amount >= config.emtl_threshold else Decimal('0.00')

    total_fees = _round(transfer_fee + vat + emtl)
    net_amount = _round(amount - total_fees)

    return TransferFeeBreakdown(
        gross_amount=amount,
        transfer_fee=transfer_fee,
        vat=vat,
        emtl=emtl,
        total_fees=total_fees,
        net_amount=net_amount,
    )


def calculate_deposit_fees(amount, config=None) -> TransferFeeBreakdown:
    """
    Calculate fees for an incoming deposit.

    Deposits are only charged EMTL/Stamp Duty (₦50 if amount >= ₦10,000).
    No transfer fee or VAT on deposits.

    Args:
        amount: The gross deposit amount
        config: Optional FeeConfiguration instance (fetched if not provided)

    Returns:
        TransferFeeBreakdown dataclass (with transfer_fee=0 and vat=0)
    """
    if config is None:
        from wallet.models import FeeConfiguration
        config = FeeConfiguration.get_active()

    amount = Decimal(str(amount))

    transfer_fee = Decimal('0.00')
    vat = Decimal('0.00')
    emtl = config.emtl_amount if amount >= config.emtl_threshold else Decimal('0.00')

    total_fees = emtl
    net_amount = _round(amount - total_fees)

    return TransferFeeBreakdown(
        gross_amount=amount,
        transfer_fee=transfer_fee,
        vat=vat,
        emtl=emtl,
        total_fees=total_fees,
        net_amount=net_amount,
    )


def calculate_payment_link_fees(amount, config=None) -> PaymentLinkFeeBreakdown:
    """
    Calculate fees for a payment link contribution.

    Fee structure:
    - Commission: 5% of amount (charged to link owner/receiver)
    - VAT: 7.5% of commission (NOT of principal)

    Args:
        amount: The gross contribution amount
        config: Optional FeeConfiguration instance (fetched if not provided)

    Returns:
        PaymentLinkFeeBreakdown dataclass
    """
    if config is None:
        from wallet.models import FeeConfiguration
        config = FeeConfiguration.get_active()

    amount = Decimal(str(amount))

    # Commission on gross amount
    commission = _round(amount * config.payment_link_commission_rate)

    # VAT on commission (NOT on principal)
    vat_on_commission = _round(commission * config.vat_rate)

    total_fees = _round(commission + vat_on_commission)
    net_amount = _round(amount - total_fees)

    return PaymentLinkFeeBreakdown(
        gross_amount=amount,
        commission=commission,
        vat_on_commission=vat_on_commission,
        total_fees=total_fees,
        net_amount=net_amount,
    )


def settle_fees_to_platform(fees):
    """
    Settle collected fees into the platform wallet.

    Accepts TransferFeeBreakdown, PaymentLinkFeeBreakdown,
    GiftFeeBreakdown, or DisbursementFeeBreakdown.
    Skips if total fees are zero.
    """
    if fees.total_fees <= 0:
        return

    from wallet.models import PlatformWallet

    try:
        pw = PlatformWallet.get_instance()

        if isinstance(fees, GiftFeeBreakdown):
            pw.deposit(gift_fee_amount=fees.gift_fee)
        elif isinstance(fees, DisbursementFeeBreakdown):
            pw.deposit(disbursement_fee_amount=fees.disbursement_fee)
        elif isinstance(fees, PaymentLinkFeeBreakdown):
            pw.deposit(
                commission_amount=fees.commission,
                vat_amount=fees.vat_on_commission,
            )
        else:
            pw.deposit(
                fee_amount=fees.transfer_fee,
                vat_amount=fees.vat,
                emtl_amount=fees.emtl,
            )
    except Exception:
        logger.exception("Failed to settle fees to platform wallet")


# ------------------------------------------------------------------
# Gifting fees (Phase 1 & 2)
# ------------------------------------------------------------------

def calculate_gift_fees(amount, config=None) -> GiftFeeBreakdown:
    """
    Calculate fees for a baby fund gift.

    Fee structure: flat 1.5% of gross amount.
    No VAT, no EMTL — just the platform commission.

    Args:
        amount: Gross gift amount
        config: Optional FeeConfiguration (uses gift_fee_rate field)

    Returns:
        GiftFeeBreakdown dataclass
    """
    if config is None:
        from wallet.models import FeeConfiguration
        config = FeeConfiguration.get_active()

    amount = Decimal(str(amount))
    rate = getattr(config, 'gift_fee_rate', Decimal('0.015'))
    gift_fee = _round(amount * rate)
    total_fees = gift_fee
    net_amount = _round(amount - total_fees)

    return GiftFeeBreakdown(
        gross_amount=amount,
        gift_fee=gift_fee,
        total_fees=total_fees,
        net_amount=net_amount,
    )


def calculate_disbursement_fees(amount, config=None) -> DisbursementFeeBreakdown:
    """
    Calculate fees for a fund withdrawal (disbursement to bank).

    Fee structure: flat 1% of withdrawal amount.

    Args:
        amount: Withdrawal amount
        config: Optional FeeConfiguration (uses disbursement_fee_rate field)

    Returns:
        DisbursementFeeBreakdown dataclass
    """
    if config is None:
        from wallet.models import FeeConfiguration
        config = FeeConfiguration.get_active()

    amount = Decimal(str(amount))
    rate = getattr(config, 'disbursement_fee_rate', Decimal('0.01'))
    disbursement_fee = _round(amount * rate)
    total_fees = disbursement_fee
    net_amount = _round(amount - total_fees)

    return DisbursementFeeBreakdown(
        gross_amount=amount,
        disbursement_fee=disbursement_fee,
        total_fees=total_fees,
        net_amount=net_amount,
    )
