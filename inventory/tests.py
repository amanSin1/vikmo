from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Product, Inventory, Dealer, Order, OrderItem


def create_admin():
    return User.objects.create_user(username='admin', password='admin123', is_staff=True)


def create_dealer_user():
    user = User.objects.create_user(username='dealer1', password='dealer123', is_staff=False)
    dealer = Dealer.objects.create(
        user=user, name='ABC Motors', phone='9999999999',
        address='123 Street', city='Mumbai', state='Maharashtra', pincode='400001'
    )
    return user, dealer


def create_product(sku='BP-001', name='Brake Pad', price=500.00):
    return Product.objects.create(sku=sku, name=name, price=price, is_active=True)


def set_stock(product, quantity):
    product.inventory.quantity = quantity
    product.inventory.save()


class ProductModelTest(TestCase):
    def test_inventory_auto_created_on_product_creation(self):
        """Signal must auto-create inventory when product is created."""
        product = create_product()
        self.assertTrue(hasattr(product, 'inventory'))
        self.assertEqual(product.inventory.quantity, 0)

    def test_current_stock_property(self):
        product = create_product()
        set_stock(product, 50)
        self.assertEqual(product.current_stock, 50)


class OrderModelTest(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.user, self.dealer = create_dealer_user()
        self.product = create_product()
        set_stock(self.product, 100)

    def test_order_number_auto_generated(self):
        """Order number must be auto-generated in ORD-YYYYMMDD-XXXX format."""
        order = Order.objects.create(dealer=self.dealer)
        self.assertTrue(order.order_number.startswith('ORD-'))

    def test_valid_status_transitions(self):
        order = Order.objects.create(dealer=self.dealer)
        self.assertTrue(order.can_transition_to(Order.STATUS_CONFIRMED))
        self.assertFalse(order.can_transition_to(Order.STATUS_DELIVERED))
        self.assertFalse(order.can_transition_to(Order.STATUS_DRAFT))

    def test_delivered_order_no_transitions(self):
        order = Order.objects.create(dealer=self.dealer, status=Order.STATUS_DELIVERED)
        self.assertFalse(order.can_transition_to(Order.STATUS_CONFIRMED))
        self.assertFalse(order.can_transition_to(Order.STATUS_DRAFT))

    def test_line_total_auto_calculated(self):
        """line_total must be quantity x unit_price."""
        order = Order.objects.create(dealer=self.dealer)
        item = OrderItem.objects.create(
            order=order, product=self.product,
            quantity=5, unit_price=500.00
        )
        self.assertEqual(float(item.line_total), 2500.00)

    def test_order_total_auto_calculated(self):
        """Order total must be sum of all line totals."""
        order = Order.objects.create(dealer=self.dealer)
        OrderItem.objects.create(order=order, product=self.product, quantity=5, unit_price=500.00)
        order.refresh_from_db()
        self.assertEqual(float(order.total_amount), 2500.00)

    def test_unit_price_locked_at_creation(self):
        """unit_price must be locked at order creation, not change with product price."""
        order = Order.objects.create(dealer=self.dealer)
        item = OrderItem.objects.create(
            order=order, product=self.product,
            quantity=1, unit_price=self.product.price
        )
        original_price = float(item.unit_price)
        # Change product price
        self.product.price = 999.00
        self.product.save()
        # Item price must stay the same
        item.refresh_from_db()
        self.assertEqual(float(item.unit_price), original_price)

    def test_is_editable_only_for_draft(self):
        draft = Order.objects.create(dealer=self.dealer, status=Order.STATUS_DRAFT)
        confirmed = Order.objects.create(dealer=self.dealer, status=Order.STATUS_CONFIRMED)
        delivered = Order.objects.create(dealer=self.dealer, status=Order.STATUS_DELIVERED)
        self.assertTrue(draft.is_editable)
        self.assertFalse(confirmed.is_editable)
        self.assertFalse(delivered.is_editable)


class OrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_admin()
        self.user, self.dealer = create_dealer_user()
        self.product = create_product()
        set_stock(self.product, 100)

    def _login_dealer(self):
        self.client.force_authenticate(user=self.user)

    def _login_admin(self):
        self.client.force_authenticate(user=self.admin)

    def test_dealer_can_create_order(self):
        self._login_dealer()
        response = self.client.post('/api/orders/', {
            'notes': 'test order',
            'items': [{'product': self.product.id, 'quantity': 10}]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')

    def test_confirm_order_deducts_stock(self):
        """Confirming order must deduct stock correctly."""
        self._login_dealer()
        # Create order
        order = Order.objects.create(dealer=self.dealer)
        OrderItem.objects.create(order=order, product=self.product, quantity=10, unit_price=500)

        # Confirm it
        response = self.client.post(f'/api/orders/{order.id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Stock must be reduced
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.quantity, 90)

        # Order must be confirmed
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)

    def test_confirm_fails_insufficient_stock(self):
        """Confirming order with insufficient stock must fail with clear error."""
        self._login_dealer()
        order = Order.objects.create(dealer=self.dealer)
        OrderItem.objects.create(order=order, product=self.product, quantity=999, unit_price=500)

        response = self.client.post(f'/api/orders/{order.id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock_errors', response.data)
        self.assertEqual(response.data['stock_errors'][0]['available'], 100)
        self.assertEqual(response.data['stock_errors'][0]['requested'], 999)

        # Stock must NOT be deducted
        self.product.inventory.refresh_from_db()
        self.assertEqual(self.product.inventory.quantity, 100)

    def test_cannot_edit_confirmed_order(self):
        """Confirmed orders must be locked from editing."""
        self._login_dealer()
        order = Order.objects.create(dealer=self.dealer, status=Order.STATUS_CONFIRMED)
        response = self.client.put(f'/api/orders/{order.id}/', {'notes': 'hacking'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be edited', response.data['error'])

    def test_invalid_transition_delivered_to_confirmed(self):
        """Delivered order must not transition back."""
        self._login_dealer()
        order = Order.objects.create(dealer=self.dealer, status=Order.STATUS_DELIVERED)
        response = self.client.post(f'/api/orders/{order.id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dealer_cannot_see_other_dealer_orders(self):
        """Dealers must only see their own orders."""
        other_user = User.objects.create_user(username='other', password='pass123')
        other_dealer = Dealer.objects.create(
            user=other_user, name='XYZ Garage', phone='8888888888',
            address='456 Road', city='Delhi', state='Delhi', pincode='110001'
        )
        other_order = Order.objects.create(dealer=other_dealer)

        self._login_dealer()
        response = self.client.get('/api/orders/')
        order_ids = [o['id'] for o in response.data['results']]
        self.assertNotIn(other_order.id, order_ids)

    def test_dealer_cannot_access_inventory(self):
        """Inventory endpoint must be admin only."""
        self._login_dealer()
        response = self.client.get('/api/inventory/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_endpoint_admin_only(self):
        """Summary endpoint must be admin only."""
        self._login_dealer()
        response = self.client.get('/api/orders/summary/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self._login_admin()
        response = self.client.get('/api/orders/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_orders', response.data)
        self.assertIn('total_confirmed_revenue', response.data)