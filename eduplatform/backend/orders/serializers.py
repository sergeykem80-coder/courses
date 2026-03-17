"""
Serializers for the orders app.
"""
from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for viewing orders."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.SlugField(source='course.slug', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display_ru', 
        read_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email', 'course', 'course_title', 'course_slug',
            'amount', 'currency', 'status', 'status_display',
            'robokassa_inv_id', 'robokassa_out_sum', 'payment_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new order."""
    
    class Meta:
        model = Order
        fields = ['course', 'amount', 'currency']
    
    def create(self, validated_data):
        # This is typically called from PaymentViewSet
        return super().create(validated_data)
