"""
Models for the orders app.

Defines Order model for tracking course purchases.
"""
from django.db import models
from django.conf import settings
from courses.models import Course


class Order(models.Model):
    """Order model for tracking course purchases and payments."""
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменён'),
        ('refunded', 'Возврат'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Пользователь"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="Курс"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Сумма"
    )
    currency = models.CharField(
        max_length=3, 
        default='RUB', 
        verbose_name="Валюта"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Статус"
    )
    
    # Robokassa data
    robokassa_inv_id = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="ID заказа Robokassa"
    )
    robokassa_out_sum = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Сумма оплаты Robokassa"
    )
    robokassa_signature = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Подпись Robokassa"
    )
    payment_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата оплаты"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        db_table = 'orders'
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.email} - {self.course.title}"
    
    def get_status_display_ru(self):
        """Get Russian display name for status."""
        return dict(self.STATUS_CHOICES)[self.status]
