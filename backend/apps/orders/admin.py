"""
Django Admin конфигурация для приложения Orders.
Управление заказами и платежами через Robokassa.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка для управления заказами и платежами"""
    
    list_display = (
        'order_id_link',
        'user', 
        'course', 
        'amount', 
        'status', 
        'payment_date',
        'created_at',
        'status_badge'
    )
    list_filter = ('status', 'currency', 'payment_date', 'created_at', 'course')
    search_fields = (
        'user__email', 
        'user__username', 
        'course__title', 
        'robokassa_inv_id'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = (
        'robokassa_inv_id', 
        'robokassa_out_sum', 
        'robokassa_signature',
        'payment_date',
        'created_at',
        'updated_at',
        'user_link',
        'course_link'
    )
    
    fieldsets = (
        ('Информация о заказе', {
            'fields': (
                'user',
                'course',
                'amount',
                'currency',
                'status',
            ),
        }),
        ('Данные Robokassa', {
            'fields': (
                'robokassa_inv_id',
                'robokassa_out_sum',
                'robokassa_signature',
                'payment_date',
            ),
            'classes': ('collapse',),
        }),
        ('Ссылки', {
            'fields': (
                'user_link',
                'course_link',
            ),
            'classes': ('collapse',),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'mark_as_paid', 
        'mark_as_pending', 
        'mark_as_cancelled',
        'grant_course_access'
    ]
    
    def order_id_link(self, obj):
        """Ссылка на детальную страницу заказа"""
        url = reverse('admin:orders_order_change', args=[obj.pk])
        return format_html('<a href="{}">#{}</a>', url, obj.id)
    order_id_link.short_description = 'ID'
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Пользователь'
    
    def course_link(self, obj):
        """Ссылка на курс"""
        url = reverse('admin:courses_course_change', args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Курс'
    
    def status_badge(self, obj):
        """Цветной бейдж статуса заказа"""
        colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'cancelled': '#dc3545',
            'refunded': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        status_labels = {
            'pending': 'Ожидает оплаты',
            'paid': 'Оплачен',
            'cancelled': 'Отменён',
            'refunded': 'Возврат',
        }
        label = status_labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; '
            'border-radius:3px; font-size:12px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Статус'
    
    def mark_as_paid(self, request, queryset):
        """Массовое действие: Отметить как оплаченные"""
        from datetime import timezone
        from apps.access.models import UserCourseAccess
        
        count = 0
        for order in queryset.filter(status='pending'):
            order.status = 'paid'
            order.payment_date = timezone.now()
            order.save()
            
            # Выдаём доступ к курсу
            UserCourseAccess.objects.get_or_create(
                user=order.user,
                course=order.course,
                defaults={'granted_by': request.user}
            )
            count += 1
        
        self.message_user(request, f'{count} заказ(а/ов) отмечено как оплаченные. Доступ выдан.')
    mark_as_paid.short_description = 'Отметить как оплаченные и выдать доступ'
    
    def mark_as_pending(self, request, queryset):
        """Массовое действие: Вернуть в ожидание оплаты"""
        updated = queryset.update(status='pending', payment_date=None)
        self.message_user(request, f'{updated} заказ(а/ов) возвращено в ожидание.')
    mark_as_pending.short_description = 'Вернуть в ожидание оплаты'
    
    def mark_as_cancelled(self, request, queryset):
        """Массовое действие: Отменить заказы"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} заказ(а/ов) отменено.')
    mark_as_cancelled.short_description = 'Отменить выбранные'
    
    def grant_course_access(self, request, queryset):
        """Массовое действие: Выдать доступ к курсам для оплаченных заказов"""
        from apps.access.models import UserCourseAccess
        
        count = 0
        for order in queryset.filter(status='paid'):
            access, created = UserCourseAccess.objects.get_or_create(
                user=order.user,
                course=order.course,
                defaults={'granted_by': request.user}
            )
            if created:
                count += 1
        
        self.message_user(request, f'Доступ выдан для {count} пользователей.')
    grant_course_access.short_description = 'Выдать доступ к курсам'
    
    # Статистика в changelist
    def changelist_view(self, request, extra_context=None):
        """Добавление статистики в список заказов"""
        from django.db.models import Sum, Count
        
        extra_context = extra_context or {}
        
        # Общая статистика
        stats = {
            'total_orders': Order.objects.count(),
            'paid_orders': Order.objects.filter(status='paid').count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'total_revenue': Order.objects.filter(
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        extra_context['stats'] = stats
        return super().changelist_view(request, extra_context=extra_context)


# Регистрация кастомного шаблона для changelist с статистикой
OrderAdmin.change_list_template = 'admin/orders/order/change_list_with_stats.html'
