from django.contrib import admin
from .models import UserProfile, Transaction, FraudRule

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'transaction_type', 'risk_score', 'is_fraud', 'status', 'created_at')
    list_filter = ('is_fraud', 'status', 'transaction_type')
    search_fields = ('user__username', 'transaction_id', 'merchant_name')
    readonly_fields = ('transaction_id', 'risk_score', 'is_fraud', 'fraud_reasons', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_as_reviewed']

    @admin.action(description='Mark selected as reviewed')
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='APPROVED')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'account_balance', 'created_at')
    search_fields = ('user__username',)


@admin.register(FraudRule)
class FraudRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_name', 'is_active', 'threshold_value')
    list_editable = ('is_active', 'threshold_value')
