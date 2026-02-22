from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, Inventory


@receiver(post_save, sender=Product)
def create_inventory_for_product(sender, instance, created, **kwargs):
    """
    Automatically create an Inventory record whenever a new Product is created.
    This ensures every product always has exactly one inventory record.
    Initial stock is 0 — admin must manually update it.
    """
    if created:
        Inventory.objects.create(product=instance, quantity=0)