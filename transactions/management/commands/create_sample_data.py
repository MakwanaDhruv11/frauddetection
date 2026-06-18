from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from transactions.models import UserProfile, Transaction, FraudRule
from transactions.fraud_engine import FraudDetectionEngine
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates sample users, transactions and fraud rules'

    def handle(self, *args, **kwargs):
        engine = FraudDetectionEngine()

        # Create 2 test users
        users_data = ['testuser1', 'testuser2']
        users = []
        for username in users_data:
            user, created = User.objects.get_or_create(
                username=username, 
                defaults={"email": f"{username}@example.com"}
            )
            if created:
                user.set_password("Test@1234")
                user.save()
                UserProfile.objects.create(user=user, phone_number="1234567890", account_balance=10000.00)
            users.append(user)
            self.stdout.write(self.style.SUCCESS(f'User {username} created/retrieved.'))

        # Create 3 Fraud Rules
        rules = [
            {"name": "High Amount Check", "desc": "Check for amount > 50000", "threshold": 50000.00},
            {"name": "Rapid Transactions", "desc": "More than 5 transactions in 10 mins", "threshold": 5.00},
            {"name": "Suspicious Location", "desc": "Check for unknown/VPN locations", "threshold": 0.00},
        ]
        
        for rule in rules:
            FraudRule.objects.get_or_create(
                rule_name=rule["name"],
                defaults={
                    "description": rule["desc"],
                    "threshold_value": Decimal(str(rule["threshold"])),
                    "is_active": True
                }
            )
        self.stdout.write(self.style.SUCCESS('3 Fraud rules created/retrieved.'))

        # Create 5 sample transactions for each user (mix of normal and fraud ones)
        transactions_data = [
            {"amount": 150.00, "type": "PAYMENT", "merchant": "Coffee Shop", "location": "New York"},
            # High amount + suspicious location -> high risk / fraud
            {"amount": 120000.00, "type": "TRANSFER", "merchant": "Unknown", "location": "VPN"}, 
            {"amount": 45.00, "type": "PAYMENT", "merchant": "Bookstore", "location": "New York"},
            # Suspicious round amount -> slightly elevated risk
            {"amount": 10000.00, "type": "WITHDRAWAL", "merchant": "ATM", "location": "New York"}, 
            {"amount": 20.00, "type": "DEPOSIT", "merchant": "Grocery", "location": "New York"},
        ]

        for user in users:
            for tx_data in transactions_data:
                tx = Transaction(
                    user=user,
                    amount=Decimal(str(tx_data["amount"])),
                    transaction_type=tx_data["type"],
                    merchant_name=tx_data["merchant"],
                    location=tx_data["location"]
                )
                
                # Save first to establish the created_at / PK
                tx.save()
                
                # Analyze using fraud engine
                tx = engine.analyze(user, tx)
                tx.save()
                
            self.stdout.write(self.style.SUCCESS(f'5 Transactions created for {user.username}.'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))
