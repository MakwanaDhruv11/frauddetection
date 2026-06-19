from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Transaction, FraudRule


class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=20, write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        """
        Validate that the email is unique across all users.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """
        Create a new User and their associated UserProfile.
        """
        phone_number = validated_data.pop('phone_number')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save()
    
        UserProfile.objects.create(
        user=user, 
        phone_number=phone_number
    )
        
        return user


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'amount', 'transaction_type', 'merchant_name', 
            'location', 'ip_address', 'device_id'
        ]

    def validate_amount(self, value):
        """
        Amount must be > 0 and <= 500000.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        if value > 500000:
            raise serializers.ValidationError("Amount cannot exceed 500000.")
        return value


class TransactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'amount', 'transaction_type', 'merchant_name', 
            'is_fraud', 'risk_score', 'fraud_reasons', 'status', 'created_at'
        ]
        read_only_fields = fields


class FraudRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudRule
        fields = '__all__'
