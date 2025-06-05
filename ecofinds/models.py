from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import math
import os

class UserProfile(models.Model):
    PAYMENT_PREFERENCE_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('bn', 'Bengali'),
        ('te', 'Telugu'),
        ('mr', 'Marathi'),
        ('ta', 'Tamil'),
        ('gu', 'Gujarati'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
        ('pa', 'Punjabi'),
        ('other', 'Other'),
    ]
    
    COMMUNICATION_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('call', 'Phone Call'),
        ('sms', 'SMS'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ecofinds_profile', default=None)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_seller_verified = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='en')
    payment_preference = models.CharField(max_length=10, choices=PAYMENT_PREFERENCE_CHOICES, default='bank')
    bank_account = models.CharField(max_length=50, blank=True)
    paypal_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('used', 'Acceptable'),
    ]
    
    LISTING_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('auction', 'Auction'),
    ]
    
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    condition = models.CharField(max_length=4, choices=CONDITION_CHOICES, default='good')
    quantity = models.IntegerField(default=1)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    date = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Listing Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    
    # Auction Specific Fields
    listing_type = models.CharField(max_length=7, choices=LISTING_TYPE_CHOICES, default='fixed')
    auction_end_date = models.DateTimeField(null=True, blank=True)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    def __str__(self):
        return f"Image for {self.product.title}"

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ecofinds_cartitems', default=None)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.title} in {self.user.username}'s cart"

class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=10, choices=UserProfile.PAYMENT_PREFERENCE_CHOICES, default='bank')
    payment_status = models.CharField(max_length=20, default='pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} purchased {self.product.title}"

class SellerReview(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('seller', 'reviewer')
    
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.seller.username}"

class AuctionBid(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bids', null=True, blank=True)
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-amount']
    
    def __str__(self):
        return f"Bid of ₹{self.amount} by {self.bidder.username} on {self.product.title}"

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    related_purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Ticket #{self.id}: {self.subject}"

class TicketResponse(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_staff_response = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Response to Ticket #{self.ticket.id} by {self.user.username}" 