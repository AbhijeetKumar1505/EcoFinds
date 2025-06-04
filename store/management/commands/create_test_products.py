from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ecofinds.models import Product, Category
from django.utils.text import slugify
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test products for development'

    def handle(self, *args, **kwargs):
        # Clear all products, categories, and non-superuser accounts
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_admin=False, is_superadmin=False).delete()

        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()

        # Create categories
        categories = {
            'Electronics': 'electronics',
            'Clothing': 'clothing',
            'Books': 'books',
            'Home': 'home',
            'Sports': 'sports'
        }
        for cat_name, cat_slug in categories.items():
            Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'{cat_name} products'}
            )

        # Test products data
        products_data = [
            {
                'title': 'iPhone 13 Pro',
                'description': 'Latest iPhone model with amazing camera and performance',
                'price': Decimal('999.99'),
                'category': 'Electronics',
                'condition': 'new',
                'quantity': 10,
                'location': 'New York, NY'
            },
            {
                'title': 'Nike Air Max',
                'description': 'Comfortable running shoes with great support',
                'price': Decimal('129.99'),
                'category': 'Sports',
                'condition': 'new',
                'quantity': 15,
                'location': 'Los Angeles, CA'
            },
            {
                'title': 'The Great Gatsby',
                'description': 'Classic novel by F. Scott Fitzgerald',
                'price': Decimal('14.99'),
                'category': 'Books',
                'condition': 'new',
                'quantity': 20,
                'location': 'Chicago, IL'
            },
            {
                'title': 'Samsung 4K TV',
                'description': '55-inch 4K Smart TV with HDR',
                'price': Decimal('699.99'),
                'category': 'Electronics',
                'condition': 'good',
                'quantity': 5,
                'location': 'Miami, FL'
            },
            {
                'title': 'Leather Jacket',
                'description': 'Genuine leather jacket, perfect for winter',
                'price': Decimal('199.99'),
                'category': 'Clothing',
                'condition': 'new',
                'quantity': 8,
                'location': 'Seattle, WA'
            },
            {
                'title': 'Yoga Mat',
                'description': 'Non-slip yoga mat with carrying strap',
                'price': Decimal('29.99'),
                'category': 'Sports',
                'condition': 'new',
                'quantity': 25,
                'location': 'Portland, OR'
            },
            {
                'title': 'Coffee Table',
                'description': 'Modern wooden coffee table with storage',
                'price': Decimal('149.99'),
                'category': 'Home',
                'condition': 'new',
                'quantity': 7,
                'location': 'Boston, MA'
            },
            {
                'title': 'Wireless Earbuds',
                'description': 'True wireless earbuds with noise cancellation',
                'price': Decimal('79.99'),
                'category': 'Electronics',
                'condition': 'new',
                'quantity': 12,
                'location': 'Austin, TX'
            },
            {
                'title': 'Running Shorts',
                'description': 'Lightweight running shorts with built-in liner',
                'price': Decimal('34.99'),
                'category': 'Sports',
                'condition': 'new',
                'quantity': 18,
                'location': 'Denver, CO'
            },
            {
                'title': 'Desk Lamp',
                'description': 'LED desk lamp with adjustable brightness',
                'price': Decimal('39.99'),
                'category': 'Home',
                'condition': 'new',
                'quantity': 15,
                'location': 'San Francisco, CA'
            }
        ]

        # Create test products
        for product_data in products_data:
            category = Category.objects.get(name=product_data['category'])
            Product.objects.create(
                title=product_data['title'],
                description=product_data['description'],
                price=product_data['price'],
                category=category,
                condition=product_data['condition'],
                quantity=product_data['quantity'],
                owner=test_user,
                location=product_data['location']
            )

        self.stdout.write(self.style.SUCCESS('Successfully created test products')) 