from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Product, Inventory, Dealer, Order, OrderItem
from .serializers import (
    ProductSerializer, InventorySerializer, InventoryUpdateSerializer,
    DealerSerializer, DealerCreateSerializer,
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('inventory').all()
    serializer_class = ProductSerializer
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'price', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Inventory.objects.select_related('product', 'last_updated_by').prefetch_related('logs').all()
    serializer_class = InventorySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'product_id'

    @action(detail=True, methods=['put'], url_path='adjust')
    def adjust(self, request, product_id=None):
        inventory = self.get_object()
        serializer = InventoryUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_quantity = inventory.quantity
        inventory.update_stock(
            new_quantity=serializer.validated_data['quantity'],
            updated_by=request.user,
            action='manual_update',
            reason=serializer.validated_data['reason']
        )
        return Response({
            'message': f'Stock updated successfully for {inventory.product.name}',
            'product': inventory.product.name,
            'previous_quantity': old_quantity,
            'new_quantity': inventory.quantity,
        })


class DealerViewSet(viewsets.ModelViewSet):
    queryset = Dealer.objects.select_related('user').all()
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return DealerCreateSerializer
        return DealerSerializer

    def create(self, request, *args, **kwargs):
        serializer = DealerCreateSerializer(data=request.data)
        if serializer.is_valid():
            dealer = serializer.save()
            return Response(DealerSerializer(dealer).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    http_method_names = ['get', 'post', 'put', 'head', 'options']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related('dealer__user').prefetch_related('items__product').all()
        if not user.is_staff:
            try:
                dealer = user.dealer_profile
                return qs.filter(dealer=dealer)
            except Dealer.DoesNotExist:
                return Order.objects.none()
        status_filter = self.request.query_params.get('status')
        dealer_filter = self.request.query_params.get('dealer')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if dealer_filter:
            qs = qs.filter(dealer__id=dealer_filter)
        return qs

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.is_staff:
            dealer_id = request.data.get('dealer_id')
            if not dealer_id:
                return Response(
                    {'error': 'Admin must provide dealer_id when creating an order.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                dealer = Dealer.objects.get(id=dealer_id)
            except Dealer.DoesNotExist:
                return Response({'error': 'Dealer not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                dealer = user.dealer_profile
            except Dealer.DoesNotExist:
                return Response(
                    {'error': 'No dealer profile found for this user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.save(dealer=dealer)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if not order.is_editable:
            return Response(
                {'error': f'Order {order.order_number} cannot be edited. Only Draft orders can be modified. Current status: {order.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'notes' in serializer.validated_data:
            order.notes = serializer.validated_data['notes']
            order.save(update_fields=['notes', 'updated_at'])

        if 'items' in serializer.validated_data:
            order.items.all().delete()
            for item_data in serializer.validated_data['items']:
                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['product'].price
                )

        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        order = self.get_object()

        if not order.can_transition_to(Order.STATUS_CONFIRMED):
            return Response(
                {'error': f'Cannot confirm order. Current status is "{order.status}". Only Draft orders can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.items.count() == 0:
            return Response(
                {'error': 'Cannot confirm an empty order. Please add items first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate ALL items stock before doing anything
        stock_errors = []
        items_to_process = []

        for item in order.items.select_related('product__inventory'):
            try:
                inventory = item.product.inventory
            except Inventory.DoesNotExist:
                stock_errors.append({
                    'product': item.product.name,
                    'sku': item.product.sku,
                    'error': 'No inventory record found for this product.'
                })
                continue

            if inventory.quantity < item.quantity:
                stock_errors.append({
                    'product': item.product.name,
                    'sku': item.product.sku,
                    'requested': item.quantity,
                    'available': inventory.quantity,
                    'error': f'Insufficient stock for {item.product.name}. Available: {inventory.quantity}, Requested: {item.quantity}'
                })
            else:
                items_to_process.append((item, inventory))

        if stock_errors:
            return Response({
                'error': 'Order confirmation failed due to insufficient stock.',
                'stock_errors': stock_errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Atomic stock deduction — all or nothing
        try:
            with transaction.atomic():
                for item, inventory in items_to_process:
                    new_quantity = inventory.quantity - item.quantity
                    inventory.update_stock(
                        new_quantity=new_quantity,
                        updated_by=request.user,
                        action='order_confirmed',
                        reason=f'Stock deducted for order {order.order_number}'
                    )
                order.status = Order.STATUS_CONFIRMED
                order.confirmed_at = timezone.now()
                order.save(update_fields=['status', 'confirmed_at', 'updated_at'])

        except Exception:
            return Response(
                {'error': 'Order confirmation failed due to a server error. No stock was deducted. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': f'Order {order.order_number} confirmed successfully. Stock has been deducted.',
            'order': OrderSerializer(order).data
        })

    @action(detail=True, methods=['post'], url_path='deliver')
    def deliver(self, request, pk=None):
        order = self.get_object()

        if not order.can_transition_to(Order.STATUS_DELIVERED):
            return Response(
                {'error': f'Cannot mark as delivered. Current status is "{order.status}". Only Confirmed orders can be marked as delivered.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = Order.STATUS_DELIVERED
        order.delivered_at = timezone.now()
        order.save(update_fields=['status', 'delivered_at', 'updated_at'])

        return Response({
            'message': f'Order {order.order_number} marked as delivered successfully.',
            'order': OrderSerializer(order).data
        })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def order_summary(request):
    """
    GET /api/orders/summary/
    Admin only — overall business summary report (bonus endpoint).
    """
    total_orders = Order.objects.count()
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))

    revenue = Order.objects.filter(
        status__in=[Order.STATUS_CONFIRMED, Order.STATUS_DELIVERED]
    ).aggregate(total=Sum('total_amount'))

    top_products = OrderItem.objects.filter(
        order__status__in=[Order.STATUS_CONFIRMED, Order.STATUS_DELIVERED]
    ).values(
        'product__name', 'product__sku'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('line_total')
    ).order_by('-total_quantity')[:5]

    low_stock = Inventory.objects.filter(quantity__lte=10).select_related('product').values(
        'product__name', 'product__sku', 'quantity'
    )

    return Response({
        'total_orders': total_orders,
        'orders_by_status': {item['status']: item['count'] for item in orders_by_status},
        'total_confirmed_revenue': revenue['total'] or 0,
        'top_5_products_by_quantity': list(top_products),
        'low_stock_alert': list(low_stock),
        'generated_at': timezone.now(),
    })


