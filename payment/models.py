from django.db import models
from django.contrib.auth.models import User
from ArnoldTONY.models import Product
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
from django.utils import timezone

# Create your models here.

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_full_name = models.CharField(max_length=200)
    shipping_email = models.CharField(max_length=200)
    shipping_phone = models.CharField(max_length=11)
    shipping_address1 = models.CharField(max_length=200)
    shipping_barangay = models.CharField(max_length=200)
    shipping_city = models.CharField(max_length=200)
    shipping_zipcode = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Shippping Address"

    def __str__(self):
        return f'Shipping Address - {str(self.id)}'
    
def create_shipping(sender, instance, created, **kwargs):
    if created:
        user_shipping = ShippingAddress(user=instance)
        user_shipping.save()

post_save.connect(create_shipping, sender=User)



#Order Model
class Order(models.Model):
    # Foreign Key
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    shipping_address = models.TextField(max_length=15000)
    amount_paid = models.DecimalField(max_digits=7, decimal_places=2)
    date_ordered = models.DateTimeField(auto_now_add=True)
    shipped = models.BooleanField(default=False)
    date_shipped = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} by {self.full_name} - {'Shipped' if self.shipped else 'Not Shipped'}"

    class Meta:
        ordering = ['-date_ordered']  # Orders listed with the most recent first


# Automatically update the `date_shipped` field
@receiver(pre_save, sender=Order)
def set_shipped_data_on_update(sender, instance, **kwargs):
    # Fetch the current state of the instance from the database
    if instance.pk:
        try:
            obj = sender._default_manager.get(pk=instance.pk)
            if instance.shipped and not obj.shipped:
                # Set `date_shipped` only when shipped status changes to True
                instance.date_shipped = timezone.now()
            elif not instance.shipped and obj.shipped:
                # Clear `date_shipped` if shipped status changes to False
                instance.date_shipped = None
        except sender.DoesNotExist:
            # This handles cases where the object does not exist (e.g., during bulk updates)
            pass

#Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    quantity = models.PositiveBigIntegerField(default=1)
    price = models.DecimalField(max_digits=7,decimal_places=2)

    def __str__(self):
        return f'Order Item - {str(self.id)}'
    

#not in use
class CustomerSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Assuming user is logged in
    description = models.TextField()
    image = models.ImageField(upload_to='customer_submissions/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Design for {self.user.username} ({self.created_at})"

class UserDesign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_design = models.ImageField(upload_to='user_designs/')  # For uploading image
    user_description = models.TextField()  # For the description

    def __str__(self):
        return f"Design by {self.user.username}"
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Associate with a user
    total = models.DecimalField(max_digits=10, decimal_places=2)  # Store total amount
    status = models.CharField(max_length=100)  # Store payment status (e.g., Completed)
    payer_id = models.CharField(max_length=100)  # Store the payer ID from PayPal
    shipping_info = models.TextField()  # Store shipping information (as text)
    transaction_date = models.DateTimeField(auto_now_add=True)  # Timestamp of the transaction

    def __str__(self):
        return f"Transaction {self.id} for {self.user.username} - {self.status}"