"""
Views for the orders app.

Provides API endpoints for order management.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer


class IsAdminOrCurator(permissions.BasePermission):
    """Permission check for admin and curator roles."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role in ['admin', 'curator']
        )


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for orders.
    - Students can view their own orders
    - Admin/Curator can view and manage all orders
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'curator']:
            return Order.objects.all().select_related('user', 'course')
        # Students can only see their own orders
        return Order.objects.filter(user=user).select_related('course')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrCurator])
    def mark_as_paid(self, request, pk=None):
        """Manually mark an order as paid (admin only)."""
        order = self.get_object()
        order.status = 'paid'
        order.save()
        
        # Grant access to the course
        from payments.models import UserCourseAccess
        UserCourseAccess.objects.get_or_create(
            user=order.user,
            course=order.course,
            defaults={'granted_by': request.user}
        )
        
        return Response({'status': 'Order marked as paid'})
