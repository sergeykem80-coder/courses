"""
Serializers for the payments app.
"""
from rest_framework import serializers
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for viewing payment orders."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.SlugField(source='course.slug', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display_ru', 
        read_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 'course', 'course_title', 'course_slug',
            'amount', 'currency', 'status', 'status_display',
            'payment_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating a new order/payment."""
    course_slug = serializers.CharField(max_length=200, required=True)
    
    def validate_course_slug(self, value):
        from courses.models import Course
        try:
            course = Course.objects.get(slug=value, status='published')
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or not published")
        return value
