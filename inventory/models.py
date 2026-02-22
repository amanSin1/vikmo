from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class Product(models.Model):
    """
    Stores product catalog information.
    Admin manages products. Dealers can only view.
    """
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique Stock Keeping Unit identifier"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Current selling price in INR"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"

    @property
    def current_stock(self):
        """Returns current available stock from linked inventory."""
        try:
            return self.inventory.quantity
        except Inventory.DoesNotExist:
            return 0


class Inventory(models.Model):
    """
    Tracks stock levels for each product.
    One-to-One with Product — exactly one inventory record per product.
    Created automatically when a Product is created (via signal).
    Admin-only manual adjustments allowed.
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current available stock quantity"
    )
    last_updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='inventory_updates',
        help_text="Admin user who last updated stock"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'
        verbose_name_plural = 'Inventories'

    def __str__(self):
        return f"{self.product.name} — Stock: {self.quantity}"

    def update_stock(self, new_quantity, updated_by, action='manual_update', reason=''):
        """
        Safely update stock and automatically create an audit log entry.
        Always use this method instead of directly setting quantity.
        """
        old_quantity = self.quantity
        self.quantity = new_quantity
        self.last_updated_by = updated_by
        self.save()

        # Auto-create audit log
        InventoryLog.objects.create(
            inventory=self,
            action=action,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            quantity_changed=new_quantity - old_quantity,
            reason=reason,
            updated_by=updated_by.username if updated_by else 'system'
        )


class InventoryLog(models.Model):
    """
    Audit trail for all inventory changes (bonus).
    Automatically created via Inventory.update_stock().
    Tracks who changed what and when.
    """
    ACTION_CHOICES = [
        ('manual_update', 'Manual Update'),
        ('order_confirmed', 'Order Confirmed (Stock Deducted)'),
        ('order_cancelled', 'Order Cancelled (Stock Restored)'),
    ]

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    quantity_changed = models.IntegerField(
        help_text="Positive = stock added, Negative = stock deducted"
    )
    reason = models.TextField(blank=True, default='')
    updated_by = models.CharField(
        max_length=255,
        default='system',
        help_text="Username of who triggered this change"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.inventory.product.name} | {self.action} | {self.quantity_changed:+d}"


class Dealer(models.Model):
    """
    Stores dealer/customer profile information.
    Each dealer is linked to a Django User account for login.
    Admin creates dealer accounts (is_staff=False users).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dealer_profile',
        help_text="Linked Django user account for authentication"
    )
    dealer_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Auto-generated unique dealer identifier e.g. DLR-0001"
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dealers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['dealer_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.dealer_code})"

    @property
    def email(self):
        """Email comes from the linked User account."""
        return self.user.email

    def generate_dealer_code(self):
        """Auto-generate dealer code in format: DLR-XXXX"""
        count = Dealer.objects.count() + 1
        return f"DLR-{count:04d}"

    def save(self, *args, **kwargs):
        if not self.dealer_code:
            self.dealer_code = self.generate_dealer_code()
            while Dealer.objects.filter(dealer_code=self.dealer_code).exists():
                unique_suffix = str(uuid.uuid4())[:4].upper()
                self.dealer_code = f"DLR-{unique_suffix}"
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Tracks orders placed by dealers.
    Status must strictly flow: Draft → Confirmed → Delivered.
    - Draft: editable, no stock impact
    - Confirmed: locked, stock deducted atomically
    - Delivered: final state
    """
    STATUS_DRAFT = 'draft'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DELIVERED = 'delivered'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_DELIVERED, 'Delivered'),
    ]

    # Enforced valid transitions — anything else is rejected
    VALID_TRANSITIONS = {
        STATUS_DRAFT: [STATUS_CONFIRMED],
        STATUS_CONFIRMED: [STATUS_DELIVERED],
        STATUS_DELIVERED: [],  # Final state
    }

    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Auto-generated: ORD-YYYYMMDD-XXXX"
    )
    dealer = models.ForeignKey(
        Dealer,
        on_delete=models.PROTECT,  # Cannot delete a dealer who has orders
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Auto-calculated sum of all line totals"
    )
    notes = models.TextField(blank=True, default='')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['dealer', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.order_number} — {self.dealer.name} [{self.status.upper()}]"

    def generate_order_number(self):
        """Generate unique order number: ORD-YYYYMMDD-XXXX"""
        date_str = timezone.now().strftime('%Y%m%d')
        today_count = Order.objects.filter(
            created_at__date=timezone.now().date()
        ).count() + 1
        return f"ORD-{date_str}-{today_count:04d}"

    def save(self, *args, **kwargs):
        # Auto-generate order number only on creation
        if not self.pk and not self.order_number:
            candidate = self.generate_order_number()
            while Order.objects.filter(order_number=candidate).exists():
                candidate = f"ORD-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            self.order_number = candidate
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status):
        """Returns True if transition from current status to new_status is valid."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def recalculate_total(self):
        """
        Recalculate total_amount from all line items.
        Called automatically whenever an OrderItem is saved or deleted.
        """
        from django.db.models import Sum
        result = self.items.aggregate(total=Sum('line_total'))
        self.total_amount = result['total'] or 0
        self.save(update_fields=['total_amount', 'updated_at'])

    @property
    def is_editable(self):
        """Only Draft orders can be modified."""
        return self.status == self.STATUS_DRAFT

    @property
    def item_count(self):
        return self.items.count()


class OrderItem(models.Model):
    """
    Individual line items within an order.
    unit_price is captured from product at time of order creation
    and never changes even if product price is updated later.
    line_total is auto-calculated as quantity × unit_price.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # Cannot delete a product that has been ordered
        related_name='order_items'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered (must be at least 1)"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Price locked at time of order — never changes"
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        editable=False,
        help_text="Auto-calculated: quantity × unit_price"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_items'
        unique_together = [('order', 'product')]  # Same product can't appear twice in one order
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def __str__(self):
        return f"{self.order.order_number} | {self.product.name} × {self.quantity} @ ₹{self.unit_price}"

    def save(self, *args, **kwargs):
        # Lock in the product price at time of order creation (only on first save)
        if not self.pk:
            self.unit_price = self.product.price
        # Always recalculate line_total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Keep parent order total in sync
        self.order.recalculate_total()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        # Recalculate after deletion
        order.recalculate_total()