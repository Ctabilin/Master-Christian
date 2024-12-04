from ArnoldTONY.models import Product, Profile

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get('cart', {})
        self.request = request

        # Initialize cart if it does not exist in the session
        if 'session_key' not in self.session:
            self.session['session_key'] = {}
        
        self.cart = self.session['session_key']

    def _update_cart_in_db(self):
        """Helper method to update the cart in the database if user is authenticated."""
        if self.request.user.is_authenticated:
            try:
                current_user = Profile.objects.get(user=self.request.user)
                cart_data = str(self.cart).replace("'", "\"")  # Convert to string and replace single quotes for JSON compatibility
                current_user.old_cart = cart_data  # Assuming 'old_cart' is a field in the Profile model
                current_user.save()
            except Profile.DoesNotExist:
                print(f"No profile found for user {self.request.user.username}")

    def db_add(self, product, quantity):
        """Add an item to the cart and reset user image and description."""
        print(f"Product: {product}, Type: {type(product)}")  # Log the product and its type for debugging
    
        if not isinstance(product, Product):
            if isinstance(product, int):  # If product is an ID (integer)
                try:
                    product = Product.objects.get(id=product)  # Fetch the product instance using the ID
                except Product.DoesNotExist:
                    raise ValueError(f"Product with ID {product} does not exist.")
            else:
                raise ValueError("Expected a Product instance or product ID.")

        product_id = product.id  # Directly use the product's ID as an integer
        product_qty = int(quantity)

    # Add or update product quantity in the cart
        if str(product_id) in self.cart:
            self.cart[str(product_id)] += product_qty  # Increment if already in cart
        else:
                self.cart[str(product_id)] = product_qty  # Add new product

    # Reset the user's image and description after adding to the cart
        if self.request.user.is_authenticated:
            try:
                user_profile = Profile.objects.get(user=self.request.user)
                user_profile.image = ''  # Clear the image
                user_profile.description = ''  # Clear the description
                user_profile.save()
            except Profile.DoesNotExist:
                print(f"No profile found for user {self.request.user.username}")

        self.session.modified = True  # Mark the session as modified
        self._update_cart_in_db()  # Update the cart in the database



    def add(self, product, quantity):
        """Add an item to the cart."""
        self.db_add(product, quantity)  # Reuse db_add method to avoid redundancy

    def __len__(self):
        """Return the number of items in the cart."""
        return sum(self.cart.values())  # Sum the quantities of all products

    def get_prods(self):
        """Return all products in the cart."""
        product_ids = list(self.cart.keys())  # Convert to list for compatibility with filter
        return Product.objects.filter(id__in=product_ids)

    def get_quants(self):
        """Return the quantities of items in the cart."""
        return self.cart

    def update(self, product, quantity):
        """Update the quantity of a specific product in the cart."""
        product_id = str(product.id) if hasattr(product, 'id') else str(product)  # Ensure product_id is a string
        product_qty = int(quantity)

        # Update quantity of the product in the cart
        if product_id in self.cart:
            self.cart[product_id] = product_qty
        else:
            raise KeyError(f"Product with ID {product_id} not found in cart.")  # Optional error handling

        self.session.modified = True  # Mark the session as modified
        self._update_cart_in_db()  # Update the cart in the database

        return self.cart

    def delete(self, product):
        """Remove a product from the cart."""
        product_id = str(product.id) if hasattr(product, 'id') else str(product)  # Ensure product_id is a string

        # Remove product from cart if it exists
        if product_id in self.cart:
            del self.cart[product_id]
        else:
            raise KeyError(f"Product with ID {product_id} not found in cart.")  # Optional error handling

        self.session.modified = True  # Mark the session as modified
        self._update_cart_in_db()  # Update the cart in the database

    def clear(self):
        """Clear the cart by deleting it from the session."""
        try:
            del self.session['session_key']  # Remove the cart from the session
        except KeyError:
            pass  # Ignore if the cart key doesn't exist

        self.session.modified = True  # Ensure session is marked as modified
        self.cart = {}  # Reset the cart object
        self._update_cart_in_db()  # Update the cart in the database

    def cart_total(self):
        """Calculate the total price of items in the cart."""
        product_ids = list(self.cart.keys())  # Convert to list for compatibility with filter
        products = Product.objects.filter(id__in=product_ids)
        quantities = self.cart
        total = 0

        # Iterate over the cart and calculate the total
        for product in products:
            product_id = str(product.id)
            quantity = quantities.get(product_id, 0)

            if product.is_sale:
                total += product.sale_price * quantity
            else:
                total += product.price * quantity

        return total
