from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from django.db.models import Q, Avg

from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from .forms import ReviewForm, ProductForm
from django.contrib import messages
from orders.models import OrderProduct, Order
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
import time
from django.contrib import messages
from accounts.models import UserProfile
from django.contrib.auth.models import User
from wishlist.models import WishlistItem, SearchQuery, PriceAlert
from django.contrib.auth import get_user_model
import datetime
import os

User = get_user_model()


def store(request, category_slug=None):
    categories = None
    products = None
    brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
    all_categories = Category.objects.all().order_by('category_name')
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    brand_filter = request.GET.get('brand')
    condition_filter = request.GET.get('condition')
    location_filter = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by', 'newest')  # Default to newest

    # Base queryset
    products = Product.objects.filter(is_available=True)

    # Apply category filter from URL first
    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=categories)
    
    # Apply additional filters
    if category_filter:
        products = products.filter(category__slug=category_filter)
    if brand_filter:
        products = products.filter(brand=brand_filter)
    if condition_filter:
        products = products.filter(condition=condition_filter)
    if location_filter:
        products = products.filter(location__icontains=location_filter)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviewrating__rating')).order_by('-avg_rating')
    else:  # newest
        products = products.order_by('-created_date')

    # Pagination
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'all_categories': all_categories,
        'brands': brands,
        'conditions': Product.CONDITION_CHOICES,
        'locations': Product.objects.values_list('location', flat=True).distinct().order_by('location'),
        'selected_category': category_filter or category_slug,
        'selected_brand': brand_filter,
        'selected_condition': condition_filter,
        'selected_location': location_filter,
        'min_price': min_price,
        'max_price': max_price,
        'selected_sort': sort_by,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    
    # Get seller reviews
    seller_reviews = ReviewRating.objects.filter(
        product__created_by=single_product.created_by,
        status=True
    ).exclude(product=single_product)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'seller_reviews': seller_reviews,
        'product_gallery': product_gallery,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    products = Product.objects.filter(is_available=True)
    product_count = 0
    
    if 'q' in request.GET:
        q = request.GET['q']
        if q:
            products = products.filter(
                Q(description__icontains=q) | 
                Q(title__icontains=q) |
                Q(category__category_name__icontains=q) |
                Q(brand__icontains=q)
            )
            product_count = products.count()
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    brand_filter = request.GET.get('brand')
    condition_filter = request.GET.get('condition')
    location_filter = request.GET.get('location')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Apply additional filters
    if category_filter:
        products = products.filter(category__slug=category_filter)
    if brand_filter:
        products = products.filter(brand=brand_filter)
    if condition_filter:
        products = products.filter(condition=condition_filter)
    if location_filter:
        products = products.filter(location__icontains=location_filter)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Order products by creation date
    products = products.order_by('-created_date')

    # Pagination
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = {
        'products': paged_products,
        'product_count': product_count,
        'all_categories': Category.objects.all().order_by('category_name'),
        'brands': Product.objects.values_list('brand', flat=True).distinct().order_by('brand'),
        'conditions': Product.CONDITION_CHOICES,
        'locations': Product.objects.values_list('location', flat=True).distinct().order_by('location'),
        'selected_category': category_filter,
        'selected_brand': brand_filter,
        'selected_condition': condition_filter,
        'selected_location': location_filter,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': request.GET.get('q', ''),
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)


@login_required(login_url='login')
def add_product(request):
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('product_name')
        brand = request.POST.get('brand')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        condition = request.POST.get('condition')
        location = request.POST.get('location')
        images = request.FILES.getlist('images')

        # Validate required fields
        if not all([title, brand, category_id, description, price, condition, location]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('store:add_product')

        # Validate at least one image
        if not images:
            messages.error(request, 'Please upload at least one product image.')
            return redirect('store:add_product')

        try:
            # Create product
            product = Product.objects.create(
                title=title,
                slug=slugify(title),
                brand=brand,
                category_id=category_id,
                description=description,
                price=price,
                condition=condition,
                location=location,
                is_available=True,
                created_by=request.user,
                stock=1,
                images=images[0]
            )

            # Save additional images
            for image in images[1:]:
                ProductGallery.objects.create(
                    product=product,
                    image=image
                )

            messages.success(request, 'Product added successfully!')
            return redirect('store:store')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            return redirect('store:add_product')

    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'store/add_product.html', context)


@login_required(login_url='accounts:login')
def submit_seller_review(request, seller_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            seller = User.objects.get(id=seller_id)
            reviews = ReviewRating.objects.filter(user=request.user, product__created_by=seller)
            
            if reviews.exists():
                # Update existing review
                review = reviews.first()
                review.rating = request.POST.get('rating')
                review.subject = request.POST.get('subject')
                review.review = request.POST.get('review')
                review.status = True
                review.save()
                messages.success(request, 'Thank you! Your seller review has been updated.')
            else:
                # Create new review
                ReviewRating.objects.create(
                    user=request.user,
                    product=Product.objects.filter(created_by=seller).first(),  # Use first product as reference
                    rating=request.POST.get('rating'),
                    subject=request.POST.get('subject'),
                    review=request.POST.get('review'),
                    status=True
                )
                messages.success(request, 'Thank you! Your seller review has been submitted.')
        except Exception as e:
            messages.error(request, 'Your review could not be submitted. Please try again.')
            print(f"Error submitting seller review: {e}")
    
    return redirect(url)


@login_required(login_url='accounts:login')
def wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user, is_active=True)
    search_queries = SearchQuery.objects.filter(user=request.user, is_active=True)
    price_alerts = PriceAlert.objects.filter(user=request.user, is_active=True)
    
    context = {
        'wishlist_items': wishlist_items,
        'search_queries': search_queries,
        'price_alerts': price_alerts,
    }
    return render(request, 'store/wishlist.html', context)


@login_required(login_url='accounts:login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        messages.info(request, 'Product is already in your wishlist.')
    else:
        messages.success(request, 'Product added to wishlist successfully.')
    
    return redirect('store:product_detail', category_slug=product.category.slug, product_slug=product.slug)


@login_required(login_url='accounts:login')
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    messages.success(request, 'Product removed from wishlist successfully.')
    return redirect('store:wishlist')


@login_required(login_url='accounts:login')
def save_search_query(request):
    if request.method == 'POST':
        query = request.POST.get('query', '')
        min_price = request.POST.get('min_price')
        max_price = request.POST.get('max_price')
        category_id = request.POST.get('category')
        notification_frequency = request.POST.get('notification_frequency', 'daily')

        # Convert empty strings to None
        min_price = float(min_price) if min_price else None
        max_price = float(max_price) if max_price else None
        category_id = int(category_id) if category_id else None

        # Get or create the search query
        search_query, created = SearchQuery.objects.get_or_create(
            user=request.user,
            query=query,
            min_price=min_price,
            max_price=max_price,
            category_id=category_id,
            defaults={'notification_frequency': notification_frequency}
        )

        if not created:
            # Update existing search query
            search_query.notification_frequency = notification_frequency
            search_query.is_active = True
            search_query.save()
            messages.info(request, 'Search query updated successfully.')
        else:
            messages.success(request, 'Search query saved successfully.')

        return redirect('store:store')
    
    return redirect('store:store')


@login_required(login_url='accounts:login')
def add_price_alert(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        target_price = request.POST.get('target_price')
        notification_frequency = request.POST.get('notification_frequency', 'daily')

        if target_price:
            target_price = float(target_price)
            
            # Validate target price is less than current price
            if target_price >= product.price:
                messages.error(request, 'Target price must be less than current price.')
                return redirect('store:product_detail', category_slug=product.category.slug, product_slug=product.slug)

            # Get or create the price alert
            price_alert, created = PriceAlert.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={
                    'target_price': target_price,
                    'notification_frequency': notification_frequency
                }
            )

            if not created:
                # Update existing price alert
                price_alert.target_price = target_price
                price_alert.notification_frequency = notification_frequency
                price_alert.is_active = True
                price_alert.save()
                messages.info(request, 'Price alert updated successfully.')
            else:
                messages.success(request, 'Price alert set successfully.')

        return redirect('store:product_detail', category_slug=product.category.slug, product_slug=product.slug)
    
    return redirect('store:store')


@login_required
def my_listings(request):
    # Get all products listed by the current user
    active_listings = Product.objects.filter(created_by=request.user, is_available=True)
    inactive_listings = Product.objects.filter(created_by=request.user, is_available=False)
    
    context = {
        'active_listings': active_listings,
        'inactive_listings': inactive_listings,
    }
    return render(request, 'store/my_listings.html', context)


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('store:my_listings')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'store/edit_product.html', context)


def home(request):
    products = Product.objects.filter(is_available=True).order_by('-created_date')[:8]
    categories = Category.objects.all()[:6]
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)


@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = 0
    quantity = 0
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
    }
    return render(request, 'store/cart.html', context)


@login_required
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user is trying to buy their own product
    if product.created_by == request.user:
        messages.error(request, "You cannot buy your own listings.")
        return redirect('store:product_detail', category_slug=product.category.slug, product_slug=product.slug)
    
    try:
        cart_item = CartItem.objects.get(product=product, user=request.user)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(
            product=product,
            user=request.user,
            quantity=1
        )
    return redirect('store:cart')


@login_required
def remove_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart_item = CartItem.objects.get(product=product, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('store:cart')


@login_required
def remove_cart_item(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart_item = get_object_or_404(CartItem, product=product, user=request.user)
        cart_item.delete()
        messages.success(request, 'Item removed from cart successfully.')
    except Exception as e:
        messages.error(request, 'Error removing item from cart.')
    return redirect('store:cart')


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = 0
    quantity = 0
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    
    if request.method == 'POST':
        # Process the order
        order = Order.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address_line_1=request.POST.get('address_line_1'),
            address_line_2=request.POST.get('address_line_2', ''),
            country=request.POST.get('country'),
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            order_total=total,
            status='New',
            ip=request.META.get('REMOTE_ADDR'),
            order_note=request.POST.get('order_note', '')
        )
        
        # Generate order number
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(order.id)
        order.order_number = order_number
        order.save()
        
        for cart_item in cart_items:
            OrderProduct.objects.create(
                order=order,
                user=request.user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True
            )
        
        # Clear the cart
        cart_items.delete()
        
        messages.success(request, 'Your order has been placed successfully!')
        return redirect('store:orders')
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def profile(request):
    user = request.user
    # My Listings
    my_listings = Product.objects.filter(created_by=user)
    # My Orders (as buyer)
    my_orders = []
    try:
        from orders.models import Order, OrderProduct
        my_orders = Order.objects.filter(user=user, is_ordered=True)
    except Exception:
        pass
    # Seller/Buyer Ratings
    seller_reviews = ReviewRating.objects.filter(product__created_by=user)
    buyer_reviews = ReviewRating.objects.filter(user=user)
    seller_rating = seller_reviews.aggregate(Avg('rating'))['rating__avg']
    buyer_rating = buyer_reviews.aggregate(Avg('rating'))['rating__avg']
    context = {
        'my_listings': my_listings,
        'my_orders': my_orders,
        'seller_rating': seller_rating,
        'buyer_rating': buyer_rating,
        'user': user,
    }
    return render(request, 'store/profile.html', context)


@login_required
def orders(request):
    try:
        from orders.models import Order
        orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
        context = {
            'orders': orders,
        }
        return render(request, 'store/orders.html', context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('store:profile')


@login_required
def deactivate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, created_by=request.user)
    if request.method == 'POST':
        product.is_available = False
        product.save()
        messages.success(request, 'Product has been deactivated successfully.')
    return redirect('store:my_listings')


@login_required
def edit_profile(request):
    user = request.user
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)

    if request.method == 'POST':
        # Update user information
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        # Update profile information
        profile.phone_number = request.POST.get('phone_number', '')
        profile.address_line_1 = request.POST.get('address_line_1', '')
        profile.address_line_2 = request.POST.get('address_line_2', '')
        profile.city = request.POST.get('city', '')
        profile.state = request.POST.get('state', '')
        profile.country = request.POST.get('country', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            # Delete old profile picture if it exists
            if profile.profile_picture:
                try:
                    if os.path.isfile(profile.profile_picture.path):
                        os.remove(profile.profile_picture.path)
                except Exception as e:
                    print(f"Error deleting old profile picture: {e}")
            
            # Save new profile picture
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('store:profile')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'store/edit_profile.html', context)


@login_required
def activate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, created_by=request.user)
    if request.method == 'POST':
        product.is_available = True
        product.save()
        messages.success(request, 'Product has been activated successfully.')
    return redirect('store:my_listings')