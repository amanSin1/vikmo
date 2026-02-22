from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Inventory, InventoryLog, Dealer, Order, OrderItem


class InventoryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLog
        fields = ['id', 'action', 'quantity_before', 'quantity_after', 'quantity_changed', 'reason', 'updated_by', 'created_at']


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    logs = InventoryLogSerializer(many=True, read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'last_updated_by', 'updated_at', 'logs']
        read_only_fields = ['id', 'product', 'product_name', 'product_sku', 'last_updated_by', 'updated_at', 'logs']


class InventoryUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(required=False, default='Manual adjustment by admin')


class ProductSerializer(serializers.ModelSerializer):
    current_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'description', 'price', 'is_active', 'current_stock', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DealerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Dealer
        fields = ['id', 'dealer_code', 'name', 'username', 'email', 'phone', 'address', 'city', 'state', 'pincode', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'dealer_code', 'created_at', 'updated_at']


class DealerCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    pincode = serializers.CharField(max_length=10)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_staff=False
        )
        dealer = Dealer.objects.create(
            user=user,
            name=validated_data['name'],
            phone=validated_data['phone'],
            address=validated_data['address'],
            city=validated_data['city'],
            state=validated_data['state'],
            pincode=validated_data['pincode'],
        )
        return dealer


# ─── Order Serializers ────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    """Read serializer — shows full product info in each line item."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'line_total']
        read_only_fields = ['id', 'product_name', 'product_sku', 'unit_price', 'line_total']


class OrderItemCreateSerializer(serializers.Serializer):
    """Write serializer — dealer only provides product id and quantity."""
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)

    def validate_product(self, product):
        # Make sure product has an inventory record
        if not hasattr(product, 'inventory'):
            raise serializers.ValidationError(f"Product '{product.name}' has no inventory record.")
        return product


class OrderSerializer(serializers.ModelSerializer):
    """Read serializer — full order with all items."""
    items = OrderItemSerializer(many=True, read_only=True)
    dealer_name = serializers.CharField(source='dealer.name', read_only=True)
    dealer_code = serializers.CharField(source='dealer.dealer_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'dealer', 'dealer_name', 'dealer_code',
            'status', 'status_display', 'total_amount', 'notes',
            'item_count', 'items',
            'confirmed_at', 'delivered_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'dealer', 'dealer_name', 'dealer_code',
            'status', 'status_display', 'total_amount', 'item_count',
            'confirmed_at', 'delivered_at', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.Serializer):
    """Write serializer — create a new draft order with items."""
    notes = serializers.CharField(required=False, default='')
    items = OrderItemCreateSerializer(many=True, min_length=1)

    def validate_items(self, items):
        # Check for duplicate products in the same order
        product_ids = [item['product'].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products found. Each product can only appear once per order.")
        return items

    def create(self, validated_data):
        dealer = validated_data['dealer']
        items_data = validated_data['items']

        # Create the order
        order = Order.objects.create(
            dealer=dealer,
            notes=validated_data.get('notes', '')
        )

        # Create order items — unit_price is auto-locked from product in model
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['product'].price  # locked at creation time
            )

        return order


class OrderUpdateSerializer(serializers.Serializer):
    """Update items/notes on a DRAFT order only."""
    notes = serializers.CharField(required=False)
    items = OrderItemCreateSerializer(many=True, required=False)

    def validate_items(self, items):
        product_ids = [item['product'].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products found.")
        return items