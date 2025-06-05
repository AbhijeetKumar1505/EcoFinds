from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg, Count, F, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import UserProfile, Product, ProductImage, CartItem, Purchase
from accounts.models import Account
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.functions import Random, TruncDate, TruncMonth, TruncYear
import paypalrestsdk
from decimal import Decimal
import random
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import pyotp
from store.models import Category
from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests

# PayPal configuration
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Language choices for Indian languages
INDIAN_LANGUAGES = [
    ('hi', 'Hindi'),
    ('bn', 'Bengali'),
    ('te', 'Telugu'),
    ('mr', 'Marathi'),
    ('ta', 'Tamil'),
    ('gu', 'Gujarati'),
    ('kn', 'Kannada'),
    ('ml', 'Malayalam'),
    ('pa', 'Punjabi'),
    ('as', 'Assamese'),
    ('or', 'Odia'),
    ('sa', 'Sanskrit'),
    ('sd', 'Sindhi'),
    ('ur', 'Urdu'),
    ('ne', 'Nepali'),
    ('si', 'Sinhala'),
    ('ks', 'Kashmiri'),
    ('dv', 'Maldivian'),
    ('my', 'Burmese'),
    ('bo', 'Tibetan'),
    ('dz', 'Dzongkha'),
    ('other', 'Other'),
]

def generate_otp():
    return str(random.randint(100000, 999999))

def send_verification_email(user, token):
    subject = 'Verify your EcoFinds account'
    html_message = render_to_string('ecofinds/email/verify_email.html', {
        'user': user,
        'token': token,
    })
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        'noreply@ecofinds.com',
        [user.email],
        html_message=html_message,
    )

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        
        if Account.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        
        if Account.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('register')
        
        user = Account.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.save()
        
        # Create user profile
        profile = UserProfile.objects.create(user=user)
        profile.save()
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    
    return render(request, 'ecofinds/register.html')

def verify_account(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        user_id = request.session.get('user_id')
        
        if not user_id:
            messages.error(request, 'Invalid verification session.')
            return redirect('register')
        
        if otp == stored_otp:
            user = Account.objects.get(id=user_id)
            user.profile.is_phone_verified = True
            user.profile.save()
            
            # Clear session
            request.session.pop('otp', None)
            request.session.pop('user_id', None)
            
            messages.success(request, 'Phone number verified successfully!')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'ecofinds/verify_account.html')

def verify_email(request, token):
    try:
        user = Account.objects.get(id=request.GET.get('user'))
        if pyotp.TOTP(settings.OTP_SECRET).verify(token):
            user.profile.is_email_verified = True
            user.profile.save()
            messages.success(request, 'Email verified successfully!')
        else:
            messages.error(request, 'Invalid verification link.')
    except Account.DoesNotExist:
        messages.error(request, 'Invalid user.')
    
    return redirect('accounts:login')

def get_recommended_products(user, limit=5):
    # Get user's purchase history
    purchased_products = Purchase.objects.filter(user=user).values_list('product_title', flat=True)
    
    # Get products in the same categories as purchased products
    recommended = Product.objects.filter(
        title__in=purchased_products
    ).exclude(
        owner=user
    ).order_by('-views')[:limit]
    
    return recommended

def get_trending_sellers(limit=5):
    return Account.objects.annotate(
        rating=Avg('seller_reviews__rating'),
        product_count=Count('listings')
    ).filter(
        is_active=True,
        product_count__gt=0
    ).order_by('-rating', '-product_count')[:limit]

def home(request):
    products = Product.objects.all().filter(is_active=True)
    categories = Category.objects.all()
    
    # Get filter parameters
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    condition = request.GET.get('condition', '')
    location = request.GET.get('location', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort_by', '')
    group_by = request.GET.get('group_by', '')

    # Apply filters
    if search:
        products = products.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category:
        try:
            category_obj = Category.objects.get(id=category)
            products = products.filter(category=category_obj)
        except Category.DoesNotExist:
            pass

    if condition:
        products = products.filter(condition=condition)
    
    if location:
        products = products.filter(location__icontains=location)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)

    # Apply sorting
    if sort_by:
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-date')
        elif sort_by == 'popular':
            products = products.order_by('-views')

    # Group products if requested
    grouped_products = {}
    if group_by:
        if group_by == 'category':
            # Get all categories that have products
            categories_with_products = Category.objects.filter(product__in=products).distinct()
            for cat in categories_with_products:
                # Get products for this category
                category_products = products.filter(category=cat)
                if category_products.exists():
                    grouped_products[cat] = category_products
        elif group_by == 'condition':
            conditions = products.values_list('condition', flat=True).distinct()
            for cond in conditions:
                condition_products = products.filter(condition=cond)
                if condition_products.exists():
                    grouped_products[cond] = condition_products
        elif group_by == 'location':
            locations = products.values_list('location', flat=True).distinct()
            for loc in locations:
                location_products = products.filter(location=loc)
                if location_products.exists():
                    grouped_products[loc] = location_products

    context = {
        'products': products,
        'categories': categories,
        'grouped_products': grouped_products,
        'group_by': group_by,
        'search': search,
        'category': category,
        'condition': condition,
        'location': location,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    
    return render(request, 'home.html', context)

def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        address = request.POST.get('address', '')

        if Account.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
        else:
            user = Account.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, address=address)
            messages.success(request, "Account created! Please login.")
            return redirect('login')
    return render(request, 'ecofinds/signup.html')

@login_required
def profile(request):
    if request.method == 'POST':
        profile = request.user.profile
        
        # Update basic information
        profile.phone_number = request.POST.get('phone_number')
        profile.location = request.POST.get('location')
        profile.bio = request.POST.get('bio')
        
        # Update communication preferences
        profile.preferred_language = request.POST.get('preferred_language')
        if profile.preferred_language == 'other':
            profile.preferred_language = request.POST.get('other_language')
        profile.communication_preference = request.POST.get('communication_preference')
        
        # Update payment information
        profile.payment_preference = request.POST.get('payment_preference')
        profile.account_holder_name = request.POST.get('account_holder_name')
        profile.bank_name = request.POST.get('bank_name')
        profile.account_number = request.POST.get('account_number')
        profile.ifsc_code = request.POST.get('ifsc_code')
        profile.branch_name = request.POST.get('branch_name')
        profile.paypal_email = request.POST.get('paypal_email')
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            if profile.avatar:
                if os.path.isfile(profile.avatar.path):
                    os.remove(profile.avatar.path)
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    # Get user's listings and purchases
    active_listings = Product.objects.filter(owner=request.user, is_active=True)
    inactive_listings = Product.objects.filter(owner=request.user, is_active=False)
    total_purchases = Purchase.objects.filter(user=request.user).count()
    recent_activity = []
    
    # Add listings to activity
    for listing in active_listings[:5]:
        recent_activity.append({
            'type': 'listing',
            'title': listing.title,
            'date': listing.date,
            'status': 'active'
        })
    
    # Add purchases to activity
    for purchase in Purchase.objects.filter(user=request.user).order_by('-date')[:5]:
        recent_activity.append({
            'type': 'purchase',
            'title': purchase.product.title,
            'date': purchase.date,
            'status': purchase.payment_status
        })
    
    # Sort activity by date
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    
    return render(request, 'ecofinds/profile.html', {
        'profile': request.user.profile,
        'language_choices': INDIAN_LANGUAGES,
        'communication_choices': UserProfile.COMMUNICATION_CHOICES,
        'payment_choices': UserProfile.PAYMENT_CHOICES,
        'active_listings': active_listings,
        'inactive_listings': inactive_listings,
        'total_purchases': total_purchases,
        'recent_activity': recent_activity
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        category = request.POST['category']
        price = float(request.POST['price'])
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            messages.error(request, "Quantity must be greater than 0")
            return redirect('add_product')
        if quantity > 10:
            messages.error(request, "Maximum quantity allowed is 10")
            return redirect('add_product')

        images = request.FILES.getlist('images[]')
        if not images:
            messages.error(request, "At least one image is required")
            return redirect('add_product')
        if len(images) > 7:
            messages.error(request, "Maximum 7 images allowed")
            return redirect('add_product')

        main_image = images[0]
        new_product = Product(
            title=title,
            description=description,
            category=category,
            price=price,
            quantity=quantity,
            image=main_image,
            owner=request.user
        )
        new_product.save()

        for image in images[1:]:
            ProductImage.objects.create(filename=image, product=new_product)

        messages.success(request, "Product added!")
        return redirect('home')
    return render(request, 'ecofinds/add_product.html')

@login_required
def my_listings(request):
    products = Product.objects.filter(owner=request.user)
    return render(request, 'ecofinds/my_listings.html', {'products': products})

@login_required
def edit_product(request, id):
    product = get_object_or_404(Product, id=id, owner=request.user)
    if request.method == 'POST':
        product.title = request.POST['title']
        product.description = request.POST['description']
        product.category = request.POST['category']
        product.price = float(request.POST['price'])
        product.quantity = int(request.POST.get('quantity', 1))
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, "Product updated!")
        return redirect('my_listings')
    return render(request, 'ecofinds/edit_product.html', {'product': product})

@login_required
def delete_product(request, id):
    product = get_object_or_404(Product, id=id, owner=request.user)
    product.delete()
    messages.success(request, "Product deleted!")
    return redirect('my_listings')

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'ecofinds/product_detail.html', {'product': product})

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'ecofinds/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, "Product added to cart!")
    return redirect('cart')

@login_required
def remove_from_cart(request, product_id):
    cart_item = get_object_or_404(CartItem, user=request.user, product_id=product_id)
    cart_item.delete()
    messages.success(request, "Product removed from cart!")
    return redirect('cart')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    if request.method == 'POST':
        for item in cart_items:
            Purchase.objects.create(
                user=request.user,
                product_title=item.product.title,
                product_price=item.product.price,
                product_image=item.product.image.name
            )
        cart_items.delete()
        messages.success(request, "Checkout successful!")
        return redirect('previous_purchases')
    return render(request, 'ecofinds/checkout.html', {'cart_items': cart_items, 'total': total})

@login_required
def previous_purchases(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-date')
    return render(request, 'ecofinds/previous_purchases.html', {'purchases': purchases})

@login_required
def save_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.saved_products.filter(id=product_id).exists():
        request.user.saved_products.remove(product)
        messages.success(request, 'Product removed from saved items.')
    else:
        request.user.saved_products.add(product)
        messages.success(request, 'Product saved successfully.')
    return redirect('product_detail', product_id=product_id)

@login_required
def saved_items(request):
    saved_products = request.user.saved_products.all()
    return render(request, 'ecofinds/saved_items.html', {
        'saved_products': saved_products
    })

def recommendations(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to view personalized recommendations.')
        return redirect('login')
    
    recommended_products = get_recommended_products(request.user, limit=10)
    return render(request, 'ecofinds/recommendations.html', {
        'recommended_products': recommended_products
    })

def trending_sellers(request):
    sellers = get_trending_sellers(limit=10)
    return render(request, 'ecofinds/trending_sellers.html', {
        'sellers': sellers
    })

@login_required
def process_payment(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    
    if purchase.payment_status == 'completed':
        messages.warning(request, 'This purchase has already been paid for.')
        return redirect('purchases')
    
    if request.user.profile.payment_preference == 'paypal':
        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('payment_success')),
                "cancel_url": request.build_absolute_uri(reverse('payment_cancel'))
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": purchase.product.title,
                        "sku": str(purchase.id),
                        "price": str(purchase.total_price),
                        "currency": "USD",
                        "quantity": purchase.quantity
                    }]
                },
                "amount": {
                    "total": str(purchase.total_price),
                    "currency": "USD"
                },
                "description": f"Purchase of {purchase.product.title}"
            }]
        })
        
        if payment.create():
            # Store payment ID in session
            request.session['payment_id'] = payment.id
            request.session['purchase_id'] = purchase.id
            
            # Redirect to PayPal
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            messages.error(request, 'Error creating PayPal payment.')
            return redirect('purchases')
    
    elif request.user.profile.payment_preference == 'bank':
        # Handle bank transfer
        purchase.payment_status = 'pending'
        purchase.payment_method = 'bank'
        purchase.save()
        
        messages.success(request, 'Bank transfer details have been sent to your email.')
        return redirect('purchases')
    
    return redirect('purchases')

@login_required
def payment_success(request):
    payment_id = request.session.get('payment_id')
    purchase_id = request.session.get('purchase_id')
    
    if not payment_id or not purchase_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('purchases')
    
    payment = paypalrestsdk.Payment.find(payment_id)
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    
    if payment.execute({"payer_id": request.GET.get('PayerID')}):
        purchase.payment_status = 'completed'
        purchase.payment_method = 'paypal'
        purchase.transaction_id = payment.id
        purchase.save()
        
        messages.success(request, 'Payment completed successfully!')
    else:
        messages.error(request, 'Payment failed.')
    
    # Clear session data
    request.session.pop('payment_id', None)
    request.session.pop('purchase_id', None)
    
    return redirect('purchases')

@login_required
def payment_cancel(request):
    messages.warning(request, 'Payment was cancelled.')
    return redirect('purchases')

@login_required
def purchases(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-date')
    
    # Group purchases by month
    purchases_by_month = {}
    for purchase in purchases:
        month_key = purchase.date.strftime('%Y-%m')
        if month_key not in purchases_by_month:
            purchases_by_month[month_key] = []
        purchases_by_month[month_key].append(purchase)
    
    return render(request, 'ecofinds/purchases.html', {
        'purchases_by_month': purchases_by_month
    }) 