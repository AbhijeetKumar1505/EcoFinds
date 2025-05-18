from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
from werkzeug.utils import secure_filename
from models import db, User, Product, CartItem, Purchase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ecoFindsSuperSecretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max image size

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

with app.app_context():
    db.create_all()



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
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
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
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
        else:
            new_user = User(username=username, email=email, password=password)
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
        db.session.commit()
        flash("Profile updated!", "success")
    return render_template('profile.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        price = float(request.form['price'])

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
    products = [Product.query.get(item.product_id) for item in cart_items]
    return render_template('cart.html', products=products)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not existing:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = 0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        total += product.price
        if current_user.budget >= product.price:
            current_user.budget -= product.price
            purchase = Purchase(user_id=current_user.id,
                                product_title=product.title,
                                product_price=product.price,
                                product_image=product.image)
            db.session.add(purchase)
            db.session.delete(product)
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
    with app.app_context():
        db.create_all()
    app.run(debug=True)
