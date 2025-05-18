from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
from werkzeug.utils import secure_filename
from models import db, User, Product, CartItem, Purchase
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ecoFindsSuperSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max image size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()
        print("Database initialized successfully!")

# Initialize the database
init_db()

@app.route('/')
def home():
    query = request.args.get('query')
    category = request.args.get('category')

    if query:
        products = Product.query.filter(Product.title.ilike(f'%{query}%')).all()
    elif category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()

    # Get cart count if user logged in, else zero
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    else:
        cart_count = 0

    return render_template('home.html', products=products, cart_count=cart_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        # Try to find user by email or username
        user = User.query.filter(
            (User.email == login) | (User.username == login)
        ).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        address = request.form.get('address', '')  # Get address from form, default to empty string
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
        else:
            new_user = User(username=username, email=email, password=password, address=address)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created! Please login.", "success")
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.budget = float(request.form['budget'])
        current_user.address = request.form.get('address', '')
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename):
                # Delete old profile picture if it's not the default
                if current_user.profile_pic != 'default.jpg':
                    old_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_pic)
                    if os.path.exists(old_pic_path):
                        os.remove(old_pic_path)
                
                # Save new profile picture
                filename = secure_filename(file.filename)
                # Add timestamp to filename to make it unique
                filename = f"{current_user.id}_{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename
        
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('profile'))

    # Get dashboard data
    active_listings = Product.query.filter_by(user_id=current_user.id).count()
    total_purchases = Purchase.query.filter_by(user_id=current_user.id).count()
    
    # Get user's listings
    user_listings = Product.query.filter_by(user_id=current_user.id).all()
    
    # Get purchase history
    purchase_history = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.date.desc()).all()
    
    # Get recent activity (combining listings and purchases)
    recent_activity = []
    
    # Add recent listings
    for listing in user_listings:
        recent_activity.append({
            'title': f'Listed: {listing.title}',
            'description': f'Price: ₹{listing.price}',
            'date': listing.date.strftime('%Y-%m-%d %H:%M') if hasattr(listing, 'date') else 'N/A'
        })
    
    # Add recent purchases
    for purchase in purchase_history:
        recent_activity.append({
            'title': f'Purchased: {purchase.product_title}',
            'description': f'Amount: ₹{purchase.product_price}',
            'date': purchase.date.strftime('%Y-%m-%d %H:%M') if hasattr(purchase, 'date') else 'N/A'
        })
    
    # Sort by date and get the 5 most recent activities
    recent_activity.sort(key=lambda x: x['date'] if x['date'] != 'N/A' else '', reverse=True)
    recent_activity = recent_activity[:5]

    return render_template('profile.html',
                         active_listings=active_listings,
                         total_purchases=total_purchases,
                         user_listings=user_listings,
                         purchase_history=purchase_history,
                         recent_activity=recent_activity)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        price = float(request.form['price'])
        quantity = int(request.form.get('quantity', 1))  # Get quantity from form

        # Validate quantity
        if quantity <= 0:
            flash("Quantity must be greater than 0", "danger")
            return redirect(url_for('add'))
        if quantity > 10:
            flash("Maximum quantity allowed is 10", "danger")
            return redirect(url_for('add'))

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash("Invalid image format", "danger")
            return redirect(url_for('add'))

        new_product = Product(
            title=title,
            description=description,
            category=category,
            price=price,
            image=filename,
            quantity=quantity,
            owner=current_user
        )
        db.session.add(new_product)
        db.session.commit()
        flash("Product added!", "success")
        return redirect(url_for('home'))
    return render_template('add_product.html')

@app.route('/my_listings')
@login_required
def my_listings():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('my_listings.html', products=products)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.title = request.form['title']
        product.description = request.form['description']
        product.category = request.form['category']
        product.price = float(request.form['price'])
        
        # Handle quantity
        quantity = int(request.form.get('quantity', 1))
        if quantity <= 0:
            flash("Quantity must be greater than 0", "danger")
            return redirect(url_for('edit', id=id))
        product.quantity = quantity
        
        db.session.commit()
        flash("Product updated!", "success")
        return redirect(url_for('my_listings'))
    return render_template('edit_product.html', product=product)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted!", "info")
    return redirect(url_for('my_listings'))

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    products = []
    total = 0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:  # Check if product still exists
            products.append({
                'product': product,
                'quantity': item.quantity,
                'subtotal': product.price * item.quantity
            })
            total += product.price * item.quantity
    return render_template('cart.html', products=products, total=total)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Prevent users from buying their own products
    if product.user_id == current_user.id:
        flash("You cannot buy your own product!", "warning")
        return redirect(url_for('home'))
    
    # Check if product is still available
    if product.quantity <= 0:
        flash("Sorry, this product is out of stock!", "danger")
        return redirect(url_for('home'))
    
    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not existing:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
        db.session.commit()
        flash("Product added to cart!", "success")
    else:
        if existing.quantity < product.quantity:
            existing.quantity += 1
            db.session.commit()
            flash("Product quantity updated in cart!", "success")
        else:
            flash("Maximum available quantity reached!", "warning")
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
            flash("Item quantity decreased in cart", "info")
        else:
            db.session.delete(cart_item)
            db.session.commit()
            flash("Item removed from cart", "info")
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = 0
    
    # First check if all items are available
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product or product.quantity < item.quantity:
            flash(f"Sorry, {product.title if product else 'Some items'} are no longer available in the requested quantity!", "danger")
            return redirect(url_for('cart'))
        total += product.price * item.quantity
    
    # Then process the purchase
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if current_user.budget >= product.price * item.quantity:
            current_user.budget -= product.price * item.quantity
            product.quantity -= item.quantity
            
            # If quantity becomes 0, remove the product
            if product.quantity == 0:
                db.session.delete(product)
            else:
                db.session.add(product)
                
            purchase = Purchase(user_id=current_user.id,
                              product_title=product.title,
                              product_price=product.price * item.quantity,
                              product_image=product.image)
            db.session.add(purchase)
        else:
            flash("Insufficient budget!", "danger")
            return redirect(url_for('cart'))
            
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash(f"Purchase complete! Total: ₹{total}", "success")
    return redirect(url_for('previous_purchases'))

@app.route('/previous_purchases')
@login_required
def previous_purchases():
    purchases = Purchase.query.filter_by(user_id=current_user.id).all()
    return render_template('previous_purchases.html', purchases=purchases)

# Run app
if __name__ == '__main__':
    app.run(debug=True)
