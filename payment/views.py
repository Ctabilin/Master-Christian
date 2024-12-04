from django.shortcuts import render, redirect
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForms
from payment.models import ShippingAddress, Order, OrderItem
from payment.forms import UserDesignForm
from django.contrib.auth.models import User
from django.contrib import messages
from ArnoldTONY.models import Product, Profile
import datetime
from .models import Transaction
#import paypal
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid #unique id
from django.core.mail import send_mail
from django.utils import timezone
import json


# Create your views here.
def orders(request, pk):
    # Ensure the user is authenticated
    if request.user.is_authenticated:
        try:
            # Fetch the specific order
            order = Order.objects.get(id=pk)

            # Fetch the items related to the order
            items = OrderItem.objects.filter(order=pk)
        except Order.DoesNotExist:
            # If the order does not exist, redirect to the home page with an error message
            messages.error(request, "Order not found")
            return redirect('home')

        # Check if the user is an admin to allow status modification
        if request.user.is_superuser:
            # Admin can modify shipping status
            if request.method == "POST":
                status = request.POST.get('shipping_status')
                if status == "true":
                    order.shipped = True
                    order.date_shipped = datetime.datetime.now()
                else:
                    order.shipped = False
                    order.date_shipped = None

                # Save the changes to the order
                order.save()

                messages.success(request, "Shipping Status Updated")
                return redirect('home')

            # Render the order details and order items for the admin
            return render(request, 'payment/orders.html', {"order": order, "items": items})

        else:
            # Regular users can only view their orders (cannot modify)
            if order.user == request.user:  # Ensure the user can view only their own order
                return render(request, 'payment/orders.html', {"order": order, "items": items})

            else:
                # If the user tries to access someone else's order, redirect with error
                messages.error(request, "Access Denied")
                return redirect('home')

    else:
        messages.error(request, "Access Denied")
        return redirect('home')


def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False)
        if request.POST:
            status = request.POST['shipping_status']
            num = request.POST['num']
            now = datetime.datetime.now()
            order = Order.objects.get(id=num)  # Use get() to fetch a specific order by id
            order.shipped = True
            order.date_shipped = now
            order.save()  # Save the changes

            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, 'payment/not_shipped_dash.html', {"orders": orders})
    else:
        messages.error(request, "Access Denied")
        return redirect('home')

def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=True)
        if request.POST:
            status = request.POST['shipping_status']
            num = request.POST['num']
            order = Order.objects.get(id=num)  # Use get() to fetch a specific order by id
            order.shipped = False
            order.save()  # Save the changes

            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, 'payment/shipped_dash.html', {"orders": orders})
    else:
        messages.error(request, "Access Denied")
        return redirect('home')
    

from django.db.models import Sum

def payment_success(request):
    """Handle the payment success logic."""
    # Retrieve payment details
    payer_id = request.GET.get('PayerID')
    payment_status = request.GET.get('payment_status', 'Completed')

    # Initialize the cart
    cart = Cart(request)

    # Retrieve cart details
    cart_products = cart.get_prods()
    quantities = cart.get_quants()
    total_amount = cart.cart_total()

    # Ensure cart is not empty
    if total_amount == 0 or not cart_products:
        messages.error(request, "Your cart is empty. Please add products to your cart.")
        return redirect('cart_summary')  # Redirect to cart if it's empty

    # Ensure shipping information exists
    shipping_info = request.session.get('my_shipping')
    if not shipping_info:
        messages.error(request, "Shipping information not found. Please try again.")
        return redirect('cart')  # Redirect to cart if shipping info is missing

    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "You need to be logged in to complete the purchase.")
        return redirect('login')

    # Prepare user details
    user_email = request.user.email
    user_name = f"{request.user.first_name} {request.user.last_name}"

    # Send receipt email
    product_details = "\n".join(
        f"{product.name} - Quantity: {quantities[str(product.id)]} - Price: {product.price} PHP"
        for product in cart_products
    )
    email_subject = "Your Payment Receipt"
    email_message = (
        f"Dear {user_name},\n\n"
        f"Thank you for your recent purchase! Here are the details of your order:\n\n"
        f"Items Purchased:\n{product_details}\n\n"
        f"Total: {total_amount} PHP\n\n"
        f"Shipping Information:\n{json.dumps(shipping_info, indent=2)}\n\n"  # Format the shipping info nicely
        f"Payment Status: {payment_status}\n\n"
        f"Thank you for shopping with us!\n\n"
        f"If you have any questions, contact us at support@example.com."
    )
    try:
        send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL, [user_email])
    except Exception as e:
        messages.error(request, f"Error sending email receipt: {e}")

    # Log transaction and create order
    try:
        # Create the Order object
        order = Order.objects.create(
            user=request.user,
            full_name=shipping_info.get('full_name', user_name),
            email=user_email,
            shipping_address=shipping_info.get('shipping_address', 'N/A'),
            amount_paid=total_amount,
            date_ordered=timezone.now(),  # Use timezone.now() instead of now()
            shipped=False
        )

        # Create the OrderItems
        for product in cart_products:
            quantity = quantities[str(product.id)]
            OrderItem.objects.create(
                order=order,
                product=product,
                user=request.user,
                quantity=quantity,
                price=product.sale_price if product.is_sale else product.price
            )

        # Create the Transaction object
        try:
            Transaction.objects.create(
                user=request.user,
                total=total_amount,
                status=payment_status,
                payer_id=payer_id,
                shipping_info=json.dumps(shipping_info)  # Store shipping info as JSON
            )
        except Exception as e:
            messages.error(request, f"Error recording transaction: {e}")

    except Exception as e:
        messages.error(request, f"Error recording order: {e}")
        return redirect('cart_summary')  # Redirect back to cart if order creation fails

    # Clear the cart
    cart.clear()

    # Calculate total sales from all transactions (sum of the 'total' field in Transaction model)
    total_sales = Transaction.objects.filter(status='Completed').aggregate(Sum('total'))['total__sum'] or 0

    # Prepare data for rendering
    zipped_items = zip(cart_products, [quantities[str(product.id)] for product in cart_products])

    # Display success message
    messages.success(request, "Payment successful! A receipt has been sent to your email.")

    # Render payment success page with total sales
    return render(request, "payment/payment_success.html", {
        "total_amount": total_amount,
        "zipped_items": zipped_items,
        "shipping_info": shipping_info,
        "total_sales": total_sales  # Pass total sales to the template
    })





def payment_failed(request):
    return render(request ,"payment/payment_failed.html", {})

from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from .models import Transaction, OrderItem, Product

def sales_report(request):
    # Get the current date and time
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    first_of_month = today.replace(day=1)
    first_of_year = today.replace(month=1, day=1)
    
    # Sales Data
    sales_today = Transaction.objects.filter(
        status='Completed', transaction_date__date=today
    ).aggregate(Sum('total'))['total__sum'] or 0

    sales_yesterday = Transaction.objects.filter(
        status='Completed', transaction_date__date=yesterday
    ).aggregate(Sum('total'))['total__sum'] or 0

    sales_monthly = Transaction.objects.filter(
        status='Completed', transaction_date__gte=first_of_month
    ).aggregate(Sum('total'))['total__sum'] or 0

    sales_yearly = Transaction.objects.filter(
        status='Completed', transaction_date__gte=first_of_year
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Retrieve all completed transactions ordered by transaction date
    transactions = Transaction.objects.filter(status='Completed').order_by('-transaction_date')

    # Best-Selling Products
    best_selling_products = (
        OrderItem.objects.values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )

    # Customer Statistics
    total_customers = User.objects.count()
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    online_users = [
        session.get_decoded().get('_auth_user_id') for session in active_sessions if '_auth_user_id' in session.get_decoded()
    ]
    customers_online = User.objects.filter(id__in=online_users).count()
    new_customers_today = User.objects.filter(date_joined__date=today).count()

    # Prepare data for rendering
    return render(request, "payment/sales_report.html", {
        "transactions": transactions,
        "sales_today": sales_today,
        "sales_yesterday": sales_yesterday,
        "sales_monthly": sales_monthly,
        "sales_yearly": sales_yearly,
        "best_selling_products": best_selling_products,
        "total_customers": total_customers,
        "customers_online": customers_online,
        "new_customers_today": new_customers_today,
    })



def checkout(request):
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()

    # Initialize the shipping form
    if request.user.is_authenticated:
        shipping_user = ShippingAddress.objects.filter(user=request.user).first()
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
    else:
        shipping_form = ShippingForm(request.POST or None)

    # Flag to indicate form submission status
    shipping_saved = False

    if request.method == 'POST':
        # Check if the shipping form submit button was clicked
        if 'shipping_form_submit' in request.POST:
            # Validate and save the shipping form
            if shipping_form.is_valid():
                shipping_form.save()
                shipping_saved = True  # Indicate successful save

    return render(request, "payment/checkout.html", {
        "cart_products": cart_products,
        "quantities": quantities,
        "totals": totals,
        "shipping_form": shipping_form,
        "shipping_saved": shipping_saved,  # Pass shipping status to the template
    })


    

def billing_info(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_prods()  # Get products in the cart
        quantities = cart.get_quants()  # Get quantities of each product
        totals = cart.cart_total()  # Total amount of the cart

        my_shipping = request.POST
        request.session['my_shipping'] = my_shipping

        # PayPal form data
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': totals,
            'item_name': 'Order',
            'no_shipping': '2',
            'invoice': str(uuid.uuid4()),
            'currency_code': 'PHP',
            'notify_url': 'http://localhost:8000/your-ipn-endpoint/',
            'return_url': 'http://127.0.0.1:8000/payment/payment_success',
            'cancel_return': 'http://127.0.0.1:8000/payment/payment_failed',
        }

        paypal_form = PayPalPaymentsForm(initial=paypal_dict)

        # Handle the form when the user is authenticated
        if request.user.is_authenticated:
            billing_form = PaymentForms()

            # Debugging step: Print cart product names and their corresponding quantities
            for product, quantity in zip(cart_products, quantities):
                print(f"Product: {product.name}, Quantity: {quantity}")  # Check if quantities are correct
                quantity = int(quantity)  # Ensure quantity is an integer

                # Check stock and subtract the quantity from stock
                if product.stock >= quantity:  # Check if there's enough stock
                    print(f"Stock before: {product.stock}, Subtracting: {quantity}")  # Debug stock before update
                    product.stock -= quantity  # Decrease the stock
                    product.save()  # Save the updated stock
                    print(f"Stock after: {product.stock}")  # Debug stock after update
                else:
                    # If there's not enough stock, show an error message and redirect
                    messages.error(request, f"Not enough stock for {product.name}.")
                    return redirect('cart')  # Redirect to the cart page for adjustments

            return render(request, "payment/billing_info.html", {
                "paypal_form": paypal_form,
                "cart_products": cart_products,
                "quantities": quantities,
                "totals": totals,
                "shipping_info": request.POST,
                "billing_form": billing_form
            })
        
        else:
            billing_form = PaymentForms()
            return render(request, "payment/billing_info.html", {
                "paypal_form": paypal_form,
                "cart_products": cart_products,
                "quantities": quantities,
                "totals": totals,
                "shipping_info": request.POST,
                "billing_form": billing_form
            })

    else:
        messages.success(request, "Access Denied")
        return redirect('home')




    
def process_order(request):
    if request.POST:

        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()

        payment_form = PaymentForms(request.POST or None)

        my_shipping = request.session.get('my_shipping')
        
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']

        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_barangay']}\n{my_shipping['shipping_zipcode']}"
        amount_paid = totals

        if request.user.is_authenticated:
            user = request.user
            create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()

            #Add order 
            #Order ID
            order_id = create_order.pk
            #Product info
            for product in cart_products():
                #Product ID
                product_id  = product.id
                #Product price
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price

                #Get Quantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
                        create_order_item.save()

            #delete cart
            for key in list(request.session.keys()):
                if key == "session_key":
                    #delete key
                    del request.session[key]

            #delete cart
            for key in list(request.session.keys()):
                if key == "session_key":
            #delete key
                    del request.session[key]

            current_user = Profile.objects.filter(user__id=request.user.id)
            current_user.update(old_cart="")


            messages.success(request, "Order Placed!")
            return redirect('home')
        else:
            create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
            create_order.save()

            order_id = create_order.pk
            #Product info
            for product in cart_products():
                #Product ID
                product_id  = product.id
                #Product price
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price

                #Get Quantity
                for key,value in quantities().items():
                    if int(key) == product.id:
                        #create order item
                        create_order_item = OrderItem(order_id=order_id, product_id=product_id, quantity=value, price=price)
                        create_order_item.save()

        messages.success(request, "Order Placed!")
        return redirect('home')

        
    else:
        messages.success(request, "Access Denied")
        return redirect('home')