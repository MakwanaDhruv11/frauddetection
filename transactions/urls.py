from django.urls import path
from .views import (
    UserRegistrationView,
    TransactionCreateView,
    TransactionListView,
    TransactionDetailView,
    FraudStatsView
)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    
    # Transaction endpoints
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<uuid:transaction_id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    
    # Stats endpoints
    path('stats/', FraudStatsView.as_view(), name='fraud-stats'),
]
