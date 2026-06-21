from datetime import datetime
from app.extensions import db
from app.models import Products, ProductVariant
from constants import TOTAL_PRODUCT_STOCK, TOTAL_PRODUCT_VARIANT_STOCK

class StockService:
    @staticmethod
    def check_stock_levels(app):
        """Check stock levels with proper app context"""
        with app.app_context():
            print("\n=== STOCK CHECK STARTED ===")
            print(f"Checking stock at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            
            try:
                # Check products with low stock
                low_stock_products = Products.objects(stock_quantity__lte=TOTAL_PRODUCT_STOCK)
                print(f"\nFound {len(low_stock_products)} products with low stock:")
                for product in low_stock_products:
                    print(f"- {product.name}: {product.stock_quantity} left")
                
                # Check variants with detailed color/size info
                low_stock_variants = ProductVariant.objects(stock_quantity__lte=TOTAL_PRODUCT_VARIANT_STOCK)
                print(f"\nFound {len(low_stock_variants)} variants with low stock:")
                
                for variant in low_stock_variants:
                    product_name = variant.product_id.name if variant.product_id else "Unknown Product"
                    print(f"- {product_name}: {variant.color} (Size {variant.size}) has {variant.stock_quantity} left")
                
                print("\n=== STOCK CHECK COMPLETED ===\n")
                return True
                
            except Exception as e:
                print(f"!!! STOCK CHECK ERROR: {str(e)} !!!")
                return False