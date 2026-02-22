from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'inventory', views.InventoryViewSet, basename='inventory')
router.register(r'dealers', views.DealerViewSet, basename='dealer')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('orders/summary/', views.order_summary, name='order-summary'),
    path('', include(router.urls)),
]