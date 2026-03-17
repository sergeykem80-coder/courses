"""
Payments app URL configuration.

Includes endpoints for creating orders and handling Robokassa webhooks.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    RobokassaWebhookView,
    PaymentSuccessView,
    PaymentFailView,
)

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

app_name = 'payments'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Robokassa webhook (no authentication required)
    path('robokassa-webhook/', RobokassaWebhookView.as_view(), name='robokassa-webhook'),
    
    # Payment result pages (for redirects from Robokassa)
    path('success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('fail/', PaymentFailView.as_view(), name='payment-fail'),
]
