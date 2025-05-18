from app import app, db
from models import Product

def migrate_quantity():
    with app.app_context():
        # Add quantity column with default value 1 for existing products
        try:
            # This will add the quantity column if it doesn't exist
            db.engine.execute('ALTER TABLE product ADD COLUMN quantity INTEGER DEFAULT 1')
            print("Successfully added quantity column to products")
        except Exception as e:
            print(f"Column might already exist or error occurred: {e}")

if __name__ == '__main__':
    migrate_quantity() 