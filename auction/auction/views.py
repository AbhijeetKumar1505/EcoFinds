from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Product, Bid
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden

# Create your views here.

def product_list(request):
    products = Product.objects.all()
    return render(request, 'auction/product_list.html', {'products': products})

@login_required
def create_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        starting_price = request.POST['starting_price']
        highest_price = starting_price
        end_time = request.POST['end_time']
        product = Product.objects.create(
            name=name,
            description=description,
            starting_price=starting_price,
            highest_price=highest_price,
            end_time=end_time,
            owner=request.user
        )
        return redirect('product_list')
    return render(request, 'auction/create_product.html')

@login_required
def bid_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if timezone.now() > product.end_time:
        return HttpResponseForbidden('Auction ended!')
    if request.method == 'POST':
        amount = float(request.POST['amount'])
        if amount > float(product.highest_price):
            Bid.objects.create(product=product, bidder=request.user, amount=amount)
            product.highest_price = amount
            product.save()
            return redirect('product_list')
        else:
            return render(request, 'auction/bid_product.html', {'product': product, 'error': 'Bid must be higher than current highest price.'})
    return render(request, 'auction/bid_product.html', {'product': product})
