from django.shortcuts import render, redirect
from. models import Product, Category,Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
from payment.forms import ShippingForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db.models import Q
import json
from cart.cart import Cart
from .forms import ProductDesignForm
from django.core.mail import send_mail

# Create your views here.
def search(request):
    if request.method == "POST":
        searched = request.POST['searched']

        searched = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains=searched))

        if not searched:
            messages.success(request, "That Product Does Not Exist.....Please Try Again")
            return render(request, "search.html",{})
        else:
            return render(request, "search.html", {'searched':searched})
    else:
        return render(request, "search.html", {})

def update_info(request):
    if request.user.is_authenticated:
        # Get the current user profile
        current_user = Profile.objects.get(user__id=request.user.id)

        try:
            # Try to get the shipping address for the user
            shipping_user = ShippingAddress.objects.get(user__id=request.user.id)

        except ShippingAddress.DoesNotExist:
            # If no shipping address exists for this user, create a new one or handle the case
            shipping_user = None

        form = UserInfoForm(request.POST or None, instance=current_user)
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)

        if form.is_valid() or shipping_form.is_valid():
            form.save()
            shipping_form.save()
            messages.success(request, "Your Profile Has Been Updated.....")
            return redirect('home')

        return render(request, 'update_info.html', {'form': form, 'shipping_form': shipping_form})

    else:
        messages.success(request, "You Need To Login First!!!!!")
        return redirect('login')

def update_password(request):
    if request.user.is_authenticated:
        current_user = request.user

        if request.method == 'POST':
            form = ChangePasswordForm(current_user, request.POST)

            if form.is_valid():
                form.save()
                messages.success(request, "Your Password Has Been Updated, Please Log In Again...")
                #login(request, current_user)
                return redirect('login')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect('update_password')
        else:
            form = ChangePasswordForm(current_user)
            return render(request, "update_password.html", {'form':form})
        
    else:
        messages.success(request, "You Need To Login First!!!!!")
        return redirect('login')

def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None, instance=current_user)

        if user_form.is_valid():
            user_form.save()

            login(request, current_user)
            messages.success(request, "Your Profile Has Been Updated.....")
            return redirect('update_user')
            return render(request, "update_user.html")
        return render(request, 'update_user.html', {"user_form":user_form})
    else:
        messages.success(request, "You Need To Login First!!!!!")
        return redirect('login')



def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {"categories":categories})

def category(request, foo):
    foo = foo.replace('-','')
    try:
        category = Category.objects.get(name=foo)
        product = Product.objects.filter(category=category)
        return render(request, 'category.html',{'products':product, 'category':category})
    
    except:
        messages.success(request, ("That category dosen't exist"))
        return redirect('home')
    

def product(request, pk):
    product = Product.objects.get(pk=pk)

    # Check if the stock is 0, and notify admin
    if product.stock == 0:
        send_mail(
            'Low Stock Notification',
            f'Product "{product.name}" is out of stock.',
            'from@example.com',
            ['admin@example.com'],
            fail_silently=False,
        )
        messages.warning(request, f'The product "{product.name}" is currently out of stock.')
        return redirect('home')  # Redirect to another page (e.g., home, products listing)

    # Handle the design submission form
    if request.method == 'POST':
        # Handle Reset Design
        if 'reset_design' in request.POST:
            # Reset user design image and description on product model
            product.user_design_image = None
            product.user_description = None
            product.save()

            # Reset session data related to design
            if 'user_design_image' in request.session:
                del request.session['user_design_image']
            if 'user_description' in request.session:
                del request.session['user_description']

            messages.success(request, 'Design has been reset.')
            return redirect('product', pk=product.pk)

        # Handle new design upload or update
        user_design_image = request.FILES.get('user_design_image')
        user_description = request.POST.get('user_description')

        if user_design_image or user_description:
            # Save the design and description to the product
            product.user_design_image = user_design_image
            product.user_description = user_description
            product.save()

            # Save the design information in the session for later use
            request.session['user_design_image'] = user_design_image.name if user_design_image else None
            request.session['user_description'] = user_description if user_description else None

            messages.success(request, 'Your design has been updated.')
        
        # Add to cart logic (assumes you have a Cart model or cart session)
        if 'add_to_cart' in request.POST:
            cart = Cart(request)
            cart.add(product)

            # Reset user design after adding to cart
            product.user_design_image = None
            product.user_description = None
            product.save()

            # Clear session design info after adding to cart
            if 'user_design_image' in request.session:
                del request.session['user_design_image']
            if 'user_description' in request.session:
                del request.session['user_description']

            messages.success(request, f'{product.name} added to your cart!')
            return redirect('cart')  # Redirect to the cart page

    return render(request, 'product.html', {
        'product': product,
    })



def home(request):
    # Get products on sale
    products_on_sale = Product.objects.filter(is_sale=True)

    # Check for products with stock = 0 and notify admin
    for product in products_on_sale:
        if product.stock == 0:
            # Send an email to the admin about low stock
            send_mail(
                'Low Stock Notification',
                f'Product "{product.name}" is out of stock.',
                'from@example.com',  # Replace with your sender email
                ['admin@example.com'],  # Replace with your admin's email
                fail_silently=False,
            )

            # Optionally, display a message to the user
            messages.warning(request, f'The product "{product.name}" is currently out of stock.')

    return render(request, 'home.html', {'products': products_on_sale})

def about(request):
    return render(request, 'about.html', {})

def services(request):
    return render(request, 'services.html', {})

def shop(request):
    products = Product.objects.all()
    return render(request, 'shop.html', {'products':products})

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)

            # Retrieve the current user's profile
            current_user = Profile.objects.get(user__id=request.user.id)
            
            # Reset the image and description
            current_user.image = None  # or set a default image if needed
            current_user.description = ''  # Reset to an empty string or a default description
            current_user.save()

            # Get their saved cart from the database
            saved_cart = current_user.old_cart

            # Convert database string to Python dictionary using JSON
            if saved_cart:
                converted_cart = json.loads(saved_cart)
                
                # Initialize the cart
                cart = Cart(request)

                # Loop through the saved cart and add items to the database
                for key, value in converted_cart.items():
                    try:
                        # Ensure the key is a valid product ID
                        product_id = int(key)
                        product = Product.objects.get(id=product_id)
                        
                        # Add the product to the cart with the given quantity
                        cart.db_add(product=product, quantity=value)
                    except ValueError:
                        # Handle invalid product ID or casting errors
                        messages.error(request, f"Invalid product ID: {key}")
                    except Product.DoesNotExist:
                        # Handle case where the product doesn't exist in the database
                        messages.error(request, f"Product with ID {key} not found.")
            
            messages.success(request, "You have been logged in.")
            return redirect('home')
        else:
            messages.error(request, "There was an error logging in.")
            return redirect('login')

    else:
        return render(request, 'login.html', {})

def logout_user(request):
    if request.user.is_authenticated:
        try:
            # Get the profile for the logged-in user
            current_user = Profile.objects.get(user=request.user)

            # Debugging: Check if Profile is fetched correctly
            print(f"Resetting profile for user: {request.user.username}")

            # Reset user design image and description
            current_user.user_design_image = None  # Reset to None (or set a default image)
            current_user.user_description = ''  # Reset to empty string

            # Ensure the changes are saved to the database
            current_user.save()
            print(f"Profile reset for {request.user.username}")

        except Profile.DoesNotExist:
            # Handle case where Profile doesn't exist
            messages.warning(request, "Profile not found for the logged-in user.")
            print("Profile not found for the logged-in user.")

    # Perform the logout operation
    logout(request)

    # Display logout message
    messages.success(request, "You have been logged out....Thanks for stopping by...")

    # Redirect to home page
    return redirect('home')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("You have successfully created an account! - Please Fill Out Your User Info Below..."))
            return redirect('update_info')
        else:
            messages.success(request, ("There was a problem registering Please try again"))
            return redirect('register')

    else: 
        return render(request, 'register.html', {'form':form})
    
def user_order(request):
    if request.user.is_authenticated:
        # Fetch only the orders for the logged-in user
        orders = Order.objects.filter(user=request.user)
        
        # Since users cannot modify orders, no POST handling is required
        return render(request, 'user_order.html', {"orders": orders})
    else:
        pass

def user_order_summary(request):
        return render(request, 'user_order_summary.html', {})

def customize(request):
    return render(request, 'customize.html', {})

def customize_tshirt(request):
    return render(request, 'customize_tshirt.html', {})

def customize_bag(request):
    return render(request, 'customize_bag.html', {})

def customize_fan(request):
    return render(request, 'customize_fan.html', {})

def customize_mpad(request):
    return render(request, 'customize_mpad.html', {})
