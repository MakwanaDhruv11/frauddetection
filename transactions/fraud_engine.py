from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from .models import Transaction

class FraudDetectionEngine:
    """
    Engine to analyze transactions and determine risk scores 
    based on a set of predefined fraud detection rules.
    """

    def __init__(self):
        # List of suspicious locations
        self.suspicious_locations = ["Unknown", "Foreign", "VPN"]

    def high_amount_check(self, transaction):
        """
        1. If amount > 50000, add risk score 30, reason: "High transaction amount"
        2. If amount > 100000, add risk score 50 instead
        """
        amount = transaction.amount
        if amount > 100000:
            return 50, "High transaction amount"
        elif amount > 50000:
            return 30, "High transaction amount"
        return 0, None

    def unusual_time_check(self, transaction):
        """
        If transaction created_at hour is between 1 AM to 5 AM, add risk score 20
        """
        # If transaction hasn't been saved yet, use current time as reference
        dt = transaction.created_at if transaction.created_at else timezone.now()
        
        # Hour check: 1 AM to 5 AM inclusive
        if 1 <= dt.hour <= 5:
            return 20, "Transaction at unusual hour"
        return 0, None

    def rapid_transaction_check(self, user, transaction):
        """
        If same user made more than 5 transactions in last 10 minutes, add risk score 40
        """
        reference_time = transaction.created_at if transaction.created_at else timezone.now()
        time_threshold = reference_time - timedelta(minutes=10)
        
        # Count existing transactions in the last 10 minutes for this user
        query = Transaction.objects.filter(
            user=user,
            created_at__gte=time_threshold,
            created_at__lte=reference_time
        )
        
        # Exclude current transaction if it's already saved and we are re-analyzing
        if transaction.pk:
            query = query.exclude(pk=transaction.pk)
            
        recent_tx_count = query.count()
        
        if recent_tx_count > 5:
            return 40, "Too many transactions in short time"
        return 0, None

    def location_mismatch_check(self, transaction):
        """
        If transaction location contains suspicious words, add risk score 25
        """
        if transaction.location:
            loc_upper = transaction.location.upper()
            for susp_loc in self.suspicious_locations:
                if susp_loc.upper() in loc_upper:
                    return 25, "Suspicious location detected"
        return 0, None

    def round_amount_check(self, transaction):
        """
        If amount is exactly round number (divisible by 10000), add risk score 10
        """
        amount = transaction.amount
        if amount > 0 and amount % Decimal('10000') == 0:
            return 10, "Suspicious round amount"
        return 0, None

    def analyze(self, user, transaction):
        """
        Run all checks, sum up total risk score, update and return transaction.
        """
        total_risk_score = 0
        fraud_reasons = []

        # List of rules to execute
        rules = [
            self.high_amount_check(transaction),
            self.unusual_time_check(transaction),
            self.rapid_transaction_check(user, transaction),
            self.location_mismatch_check(transaction),
            self.round_amount_check(transaction)
        ]

        # Process rule results
        for score, reason in rules:
            if score > 0:
                total_risk_score += score
                fraud_reasons.append(reason)

        # Cap the risk score at 100 to respect the model validator
        total_risk_score = min(total_risk_score, 100)

        # Update the transaction instance
        transaction.risk_score = total_risk_score
        transaction.fraud_reasons = fraud_reasons

        # Determine status and is_fraud flag based on final score
        if total_risk_score >= 70:
            transaction.is_fraud = True
            transaction.status = 'FLAGGED'
        elif total_risk_score >= 40:
            transaction.is_fraud = False
            transaction.status = 'FLAGGED'
        else:
            transaction.is_fraud = False
            transaction.status = 'APPROVED'

        return transaction
