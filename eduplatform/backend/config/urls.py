"""
URL configuration for EduPlatform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('users.urls')),
    
    # Courses app
    path('api/courses/', include('courses.urls', namespace='courses')),
    
    # Orders app
    path('api/orders/', include('orders.urls', namespace='orders')),
    
    # Payments app (Robokassa integration)
    path('api/payments/', include('payments.urls', namespace='payments')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
