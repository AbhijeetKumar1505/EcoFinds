from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ecofinds.models import Product
from django.db import transaction

class Command(BaseCommand):
    help = 'Clears Account database and creates test products'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            # Clear Account database
            Account = get_user_model()
            Account.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Successfully cleared Account database'))

            # Create test user
            test_user = Account.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            test_user.is_active = True
            test_user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created test user'))

            # Create test products
            test_products = [
                {
                    'title': 'Vintage Leather Jacket',
                    'description': 'Classic brown leather jacket in excellent condition',
                    'price': 199.99,
                    'category': 'Clothing',
                    'condition': 'like_new',
                    'location': 'New York',
                    'views': 150,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'MacBook Pro 2019',
                    'description': '13-inch MacBook Pro with 8GB RAM and 256GB SSD',
                    'price': 899.99,
                    'category': 'Electronics',
                    'condition': 'good',
                    'location': 'San Francisco',
                    'views': 300,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Nike Air Max',
                    'description': 'White Nike Air Max sneakers, size 10',
                    'price': 89.99,
                    'category': 'Footwear',
                    'condition': 'new',
                    'location': 'Los Angeles',
                    'views': 200,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Designer Watch',
                    'description': 'Luxury watch with leather strap',
                    'price': 299.99,
                    'category': 'Accessories',
                    'condition': 'like_new',
                    'location': 'Chicago',
                    'views': 180,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Gaming Console',
                    'description': 'Latest gaming console with 2 controllers',
                    'price': 399.99,
                    'category': 'Electronics',
                    'condition': 'good',
                    'location': 'Seattle',
                    'views': 250,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Vintage Camera',
                    'description': 'Classic film camera from the 80s',
                    'price': 149.99,
                    'category': 'Electronics',
                    'condition': 'fair',
                    'location': 'Boston',
                    'views': 120,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Designer Handbag',
                    'description': 'Luxury handbag in perfect condition',
                    'price': 599.99,
                    'category': 'Accessories',
                    'condition': 'like_new',
                    'location': 'Miami',
                    'views': 220,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Smartphone',
                    'description': 'Latest model smartphone with warranty',
                    'price': 699.99,
                    'category': 'Electronics',
                    'condition': 'new',
                    'location': 'Austin',
                    'views': 280,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Vintage Vinyl Records',
                    'description': 'Collection of classic rock vinyl records',
                    'price': 79.99,
                    'category': 'Entertainment',
                    'condition': 'good',
                    'location': 'Portland',
                    'views': 90,
                    'is_active': True,
                    'owner': test_user
                },
                {
                    'title': 'Designer Sunglasses',
                    'description': 'Luxury sunglasses with case',
                    'price': 199.99,
                    'category': 'Accessories',
                    'condition': 'new',
                    'location': 'Denver',
                    'views': 160,
                    'is_active': True,
                    'owner': test_user
                }
            ]

            for product_data in test_products:
                Product.objects.create(**product_data)

            self.stdout.write(self.style.SUCCESS('Successfully created 10 test products')) 