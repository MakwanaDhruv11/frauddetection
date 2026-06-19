from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Transaction
from .serializers import (
    UserRegistrationSerializer, 
    TransactionCreateSerializer, 
    TransactionListSerializer
)
from .fraud_engine import FraudDetectionEngine


class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user_id": user.id,
                "username": user.username,
                "message": "Registration successful"
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransactionCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Initially save the transaction
            transaction = serializer.save(user=request.user)
            
            # Analyze using our fraud detection engine
            engine = FraudDetectionEngine()
            transaction = engine.analyze(request.user, transaction)
            
            # Save the updated score and status
            transaction.save()

            return Response({
                "transaction_id": transaction.transaction_id,
                "risk_score": transaction.risk_score,
                "is_fraud": transaction.is_fraud,
                "status": transaction.status,
                "fraud_reasons": transaction.fraud_reasons
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionListView(ListAPIView):
    serializer_class = TransactionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Base query: only current user's transactions
        queryset = Transaction.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Support for ?status=FLAGGED
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
            
        # Support for ?is_fraud=true
        is_fraud_param = self.request.query_params.get('is_fraud')
        if is_fraud_param is not None:
            is_fraud_val = is_fraud_param.lower() in ['true', '1', 't', 'y', 'yes']
            queryset = queryset.filter(is_fraud=is_fraud_val)
            
        return queryset


class TransactionDetailView(RetrieveAPIView):
    serializer_class = TransactionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Lookup by UUID transaction_id
        transaction_id = self.kwargs.get('transaction_id')
        obj = get_object_or_404(Transaction, transaction_id=transaction_id)
        
        # Ensure user can only view their own transaction
        if obj.user != self.request.user:
            raise PermissionDenied("You do not have permission to view this transaction.")
            
        return obj


class FraudStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        
        total_transactions = transactions.count()
        total_fraud = transactions.filter(is_fraud=True).count()
        total_flagged = transactions.filter(status='FLAGGED').count()
        
        avg_risk_result = transactions.aggregate(avg_risk=Avg('risk_score'))
        average_risk_score = avg_risk_result['avg_risk'] or 0.0

        return Response({
            "total_transactions": total_transactions,
            "total_fraud": total_fraud,
            "total_flagged": total_flagged,
            "average_risk_score": round(average_risk_score, 2)
        }, status=status.HTTP_200_OK)
