from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm, PaymentDetailsForm
from .models import Account, UserProfile
from orders.models import Order, OrderProduct
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import authenticate, login

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.conf import settings

from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests
from django.utils import timezone
import random


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            communication_preference = form.cleaned_data['communication_preference']
            preferred_language = form.cleaned_data['preferred_language']
            other_language = form.cleaned_data.get('other_language', '')

            # Check if user already exists
            if Account.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered!')
                return redirect('accounts:register')

            # Create user
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=email,
                password=password
            )

            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone_number=phone_number,
                communication_preference=communication_preference,
                preferred_language=preferred_language,
                other_language=other_language if preferred_language == 'other' else ''
            )

            # Generate verification code (6 digits)
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store verification code in user model
            user.email_verification_token = verification_code
            user.email_verification_token_created = timezone.now()
            user.save()

            # Send verification email
            mail_subject = 'Your EcoFinds Account Verification Code'
            message = f"""
Hello {first_name},

Thank you for creating an account with EcoFinds!

Your verification code is: {verification_code}

Please enter this code to verify your email address. This code will expire in 24 hours.

If you did not create an account with EcoFinds, please ignore this email.

Best regards,
The EcoFinds Team
"""
            to_email = email
            send_mail(
                subject=mail_subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )

            messages.success(request, 'Registration successful! Please check your email for the verification code.')
            return redirect('accounts:verify_email')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def verify_email(request):
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        email = request.POST.get('email')
        
        try:
            user = Account.objects.get(email=email)
            
            # Check if code is expired (24 hours)
            if user.email_verification_token_created and (timezone.now() - user.email_verification_token_created).days > 1:
                messages.error(request, 'Verification code has expired. Please request a new one.')
                return redirect('accounts:register')
            
            if user.email_verification_token == verification_code:
                user.is_active = True
                user.is_email_verified = True
                user.email_verification_token = None
                user.email_verification_token_created = None
                user.save()
                messages.success(request, 'Email verified successfully! You can now login.')
                return redirect('accounts:login')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
        except Account.DoesNotExist:
            messages.error(request, 'Invalid email address.')
    
    return render(request, 'accounts/verify_email.html')


@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # Check if token is expired (24 hours)
        if user.email_verification_token_created and (timezone.now() - user.email_verification_token_created).days > 1:
            messages.error(request, 'Activation link has expired. Please request a new one.')
            return redirect('accounts:login')
            
        user.is_active = True
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_token_created = None
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('accounts:register')


@login_required(login_url='accounts:login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    context = {
        'orders_count': orders_count,
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')


@login_required(login_url='accounts:login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required
def profile(request):
    userprofile = UserProfile.objects.get(user=request.user)
    context = {
        'userprofile': userprofile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='accounts:login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='accounts:login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        user = User.objects.get(username__exact=request.user.username)
        
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('accounts:change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('accounts:change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('accounts:change_password')
    return render(request, 'accounts/change_password.html')


@login_required(login_url='accounts:login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)


@login_required(login_url='accounts:login')
def payment_details(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = PaymentDetailsForm(request.POST, instance=userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment details saved successfully!')
            return redirect('accounts:dashboard')
    else:
        form = PaymentDetailsForm(instance=userprofile)
    
    return render(request, 'accounts/payment_details.html', {'form': form})


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    for item in cart_item:
                        item.user = user
                        item.save()
            except:
                pass

            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('store:home')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('accounts:login')
    return render(request, 'accounts/login.html')
