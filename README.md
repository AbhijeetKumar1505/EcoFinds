## EcoFinds – Empowering Sustainable Consumption through a Second-Hand Marketplace" 
Built with Flask, it features a user-friendly interface, a robust database, and a responsive design.

## Table of Contents

- [Features](#Features)
- [Screenshots](#screenshots)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Contact](#Contact)

---

# Features

- 🔍 **Browse Eco-Friendly Products:** Search and filter a curated list of eco-friendly items.
- 📝 **User Submissions:** Users can add new products and tips.
- 📊 **Database Integration:** All data is stored in a SQLite database.
- 🖼️ **Image Uploads:** Users can upload images for products.
- 🔒 **User Authentication:** Secure login and registration.
- 📱 **Responsive Design:** Works on desktop and mobile devices.

---

## Screenshots

![image](https://github.com/user-attachments/assets/9a8fa845-b413-4d76-b53b-1ae2990908f5)

---

## Demo

Try the live demo: [EcoFinds Demo](https://your-demo-link.com)

---

## Installation
requirements.txt:
```
Flask==2.3.3
Flask-Login==0.6.3
Flask-Bcrypt==1.0.1
Flask-SQLAlchemy==3.1.1
Werkzeug==3.0.1
```


### Steps

1. **Clone the repository:**

```bash
git clone https://github.com/AbhijeetKumar1505/EcoFinds.git
cd EcoFinds
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set up the database:**

```bash
flask db upgrade
# Or, for SQLite:
python setup_db.py
```

4. **Run the app:**

```bash
python app.py
```


---

## Usage

- Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)
- Register as a new user or log in.
- Browse, add, or edit eco-friendly products.
- Upload images to enhance your listings.

---

## Project Structure

```
ecofinds/
├── app.py
├── requirements.txt
├── instance/
│   └── database.db
├── static/
│   └── uploads/
│       └── EcoFInds_logo.png
    └── css/
│       └── style.css

├── templates/
│   ├── add_product.html
│   ├── base.html
│   └── cart.html
│   └──  checkout.html
│   └── edit_product.html
│   └── home.html
│   └── login.html
│   └── my_listings.html
│   └── previous_purchase.html
│   └── product_detail.html
│   └── signup.html
│   └── profile.html
├── README.md
└── ...
```

# contact
Team Number: 284
Team Members:
1. Suhail Akthar S M || 24f2002684@ds.study.iitm.ac.in
2. Abhijeet Kumar || suhailmobina95@gmail.com
3. Himanshu Rastogi || 23f2001665@ds.study.iitm.ac.in
4. Yashvi Upadhyay || 24f2007780@ds.study.iitm.ac.in

