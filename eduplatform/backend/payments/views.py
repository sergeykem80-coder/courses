"""
Views for the payments app.

Handles payment processing, Robokassa integration, and course access management.
"""
import hashlib
import logging
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404, render
from orders.models import Order
from courses.models import Course
from access.models import UserCourseAccess
from .models import PaymentNotification
from .serializers import PaymentSerializer, OrderCreateSerializer

logger = logging.getLogger('payments')


class RobokassaService:
    """Service for Robokassa payment integration."""
    
    BASE_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"
    
    def __init__(self):
        self.merchant_login = settings.ROBOKASSA_LOGIN
        self.password1 = settings.ROBOKASSA_PASSWORD1
        self.password2 = settings.ROBOKASSA_PASSWORD2
        self.is_test = getattr(settings, 'ROBOKASSA_IS_TEST', True)
    
    def _generate_signature(self, *args, password=None) -> str:
        """Generate MD5 signature for Robokassa."""
        if password is None:
            password = self.password1
        
        signature_string = ":".join(str(arg) for arg in args) + f":{password}"
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest().upper()
    
    def create_payment_url(self, order_id: int, amount: Decimal, 
                          description: str, email: str) -> str:
        """Create payment URL for Robokassa."""
        signature = self._generate_signature(
            self.merchant_login, amount, order_id
        )
        
        params = {
            'MerchantLogin': self.merchant_login,
            'OutSum': amount,
            'InvId': order_id,
            'Description': description,
            'SignatureValue': signature,
            'Email': email,
            'Culture': 'ru',
            'IsTest': 1 if self.is_test else 0,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.BASE_URL}?{query_string}"
    
    def verify_webhook_signature(self, params: dict) -> bool:
        """Verify webhook signature from Robokassa."""
        received_signature = params.get('SignatureValue', '').upper()
        
        # Robokassa uses password2 for webhook verification
        expected_signature = self._generate_signature(
            params.get('OutSum'),
            params.get('InvId'),
            password=self.password2
        )
        
        return received_signature == expected_signature


class PaymentViewSet(viewsets.ViewSet):
    """
    Payment operations.
    - Create order and get payment URL
    - View user's orders
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer
    
    def create(self, request):
        """Create a new order and return Robokassa payment URL."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_slug = request.data.get('course_slug')
        course = get_object_or_404(Course, slug=course_slug, status='published')
        
        # Check if user already has access
        existing_access = UserCourseAccess.objects.filter(
            user=request.user,
            course=course,
            is_active=True
        ).first()
        
        if existing_access:
            return Response(
                {'error': 'Вы уже имеете доступ к этому курсу'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate unique InvId (using timestamp + user_id)
        import time
        inv_id = f"{int(time.time())}_{request.user.id}"
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            course=course,
            amount=course.price,
            currency='RUB',
            robokassa_inv_id=inv_id,
            status='pending'
        )
        
        logger.info(f"Создан заказ {order.id} для пользователя {request.user.email} на сумму {order.amount}")
        
        # Generate Robokassa payment URL
        robokassa = RobokassaService()
        payment_url = robokassa.create_payment_url(
            order_id=order.id,
            amount=order.amount,
            description=f"Оплата курса: {course.title}",
            email=request.user.email
        )
        
        return Response({
            'order_id': order.id,
            'payment_url': payment_url,
            'amount': str(order.amount),
            'course_title': course.title
        })
    
    def list(self, request):
        """List user's orders."""
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = PaymentSerializer(orders, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class RobokassaWebhookView(APIView):
    """
    Webhook endpoint for Robokassa ResultURL.
    
    Robokassa sends POST request when payment is completed.
    Must return 'OK|order_id' on success or error message on failure.
    """
    permission_classes = []
    
    def post(self, request):
        params = request.POST
        logger.debug(f"Получен вебхук от Robokassa: {dict(params)}")
        
        robokassa = RobokassaService()
        
        # Verify signature
        if not robokassa.verify_webhook_signature(params):
            logger.warning(f"Неверная подпись вебхука: {params.get('InvId')}")
            return HttpResponse('Bad signature', status=400)
        
        # Get order
        try:
            order_id = int(params.get('InvId'))
            order = Order.objects.select_related('user', 'course').get(id=order_id)
        except (Order.DoesNotExist, ValueError) as e:
            logger.error(f"Заказ не найден: {params.get('InvId')}, ошибка: {e}")
            return HttpResponse('Order not found', status=404)
        
        # Check if order is already paid
        if order.status == 'paid':
            logger.info(f"Заказ {order.id} уже оплачен, возвращаем OK")
            return HttpResponse(f'OK|{order.id}')
        
        # Update order
        order.status = 'paid'
        order.payment_date = timezone.now()
        order.robokassa_out_sum = params.get('OutSum')
        order.robokassa_signature = params.get('SignatureValue')
        order.save()
        
        logger.info(f"Заказ {order.id} отмечен как оплаченный")
        
        # Grant access to course
        access, created = UserCourseAccess.objects.get_or_create(
            user=order.user,
            course=order.course,
            defaults={'granted_by': order.user}
        )
        
        if created:
            logger.info(f"Предоставлен доступ пользователю {order.user.email} к курсу {order.course.title}")
        else:
            logger.info(f"Доступ пользователя {order.user.email} к курсу {order.course.title} уже существовал")
        
        # Log payment notification
        PaymentNotification.objects.create(
            order=order,
            raw_data=dict(params),
            processed=True
        )
        
        # TODO: Send success email asynchronously
        # send_payment_success_email.delay(order.id)
        
        # Return success response for Robokassa
        return HttpResponse(f'OK|{order.id}')


class PaymentSuccessView(APIView):
    """
    Success page after payment redirect from Robokassa.
    Shows success message and link to course.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        order_id = request.GET.get('InvId')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                return render(request, 'payments/success.html', {'order': order})
            except Order.DoesNotExist:
                pass
        
        return render(request, 'payments/success.html', {'order': None})


class PaymentFailView(APIView):
    """
    Fail page after payment cancellation from Robokassa.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        order_id = request.GET.get('InvId')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                return render(request, 'payments/fail.html', {'order': order})
            except Order.DoesNotExist:
                pass
        
        return render(request, 'payments/fail.html', {'order': None})


class HealthCheckView(APIView):
    """
    Health check endpoint for Amvera monitoring.
    Returns 200 OK if application is healthy.
    """
    permission_classes = []
    
    def get(self, request):
        try:
            # Check database connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            return Response({
                'status': 'healthy',
                'database': 'connected',
                'debug': settings.DEBUG
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response({
                'status': 'unhealthy',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
