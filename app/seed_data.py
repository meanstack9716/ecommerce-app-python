from app.extensions import db
from app.models import Category, SubCategory, SubSubCategory, ProductBrands
from flask import url_for

def seed_categories():
    if Category.objects.count() > 0:
        print("Categories already exist. Skipping category seeding.")
        return

    category_data = {
        "MEN": ["Shirts", "Pants", "Shoes", "Accessories"],
        "WOMEN": ["Dresses", "Handbags", "Shoes", "Jewelry"],
        "KIDS": ["Toys", "Clothing", "Shoes"],
        "ELECTRONICS": ["Mobiles", "Laptops", "Headphones"],
        "HOME": ["Furniture", "Kitchen", "Decor"],
        "BEAUTY": ["Skincare", "Makeup", "Haircare"],
        "SPORTS": ["Equipment", "Activewear", "Footwear"],
        "TOYS": ["Action Figures", "Dolls", "Puzzles"],
        "BOOKS": ["Fiction", "Non-Fiction", "Comics"],
    }

    sub_sub_category_data = {
        "Shirts": ["Casual Shirts", "Formal Shirts"],
        "Pants": ["Jeans", "Chinos"],
        "Shoes": ["Sneakers", "Formal Shoes", "Running Shoes", "Cleats"],
        "Accessories": ["Belts", "Wallets"],
        "Dresses": ["Evening Dresses", "Casual Dresses"],
        "Handbags": ["Totes", "Clutches"],
        "Jewelry": ["Necklaces", "Earrings"],
        "Mobiles": ["Android Phones", "iPhones"],
        "Laptops": ["Gaming Laptops", "Ultrabooks"],
        "Headphones": ["Wireless", "Noise Cancelling"],
        "Furniture": ["Sofas", "Beds"],
        "Kitchen": ["Cookware", "Appliances"],
        "Decor": ["Wall Art", "Lamps"],
        "Skincare": ["Moisturizers", "Serums"],
        "Makeup": ["Lipsticks", "Foundations"],
        "Haircare": ["Shampoo", "Conditioner"],
        "Equipment": ["Dumbbells", "Treadmills"],
        "Activewear": ["Tracksuits", "Leggings"],
        "Footwear": ["Running Shoes", "Cleats"],
        "Action Figures": ["Superheroes", "Movie Characters"],
        "Dolls": ["Barbie", "Baby Dolls"],
        "Puzzles": ["Jigsaw", "3D Puzzles"],
        "Fiction": ["Novels", "Short Stories"],
        "Non-Fiction": ["Biographies", "Self-Help"],
        "Comics": ["Marvel", "DC"],
        "Car Accessories": ["Seat Covers", "Floor Mats"],
        "Bike Accessories": ["Helmets", "Bike Locks"],
        "Tools": ["Wrenches", "Screwdrivers"]
    }

    categories = {}
    subcategories = {}

    for cat_name, subcat_names in category_data.items():
        category = Category(
            name=cat_name,
            description=f"{cat_name} category description",
            img_url=f"{cat_name.lower()}.jpg"
        ).save()
        categories[cat_name] = category

        for subcat_name in subcat_names:
            subcategory = SubCategory(
                name=subcat_name,
                description=f"{subcat_name} subcategory description",
                category=category,
                img_url=f"{subcat_name.lower().replace(' ', '_')}.jpg"
            ).save()
            subcategories[subcat_name] = subcategory
            print(f"  Subcategory created: {subcat_name}")

            if subcat_name in sub_sub_category_data:
                for prod_type_name in sub_sub_category_data[subcat_name]:
                    SubSubCategory(
                        name=prod_type_name,
                        description=f"{prod_type_name} product type description",
                        category_id=category,
                        sub_category_id=subcategory,
                        img_url=f"{prod_type_name.lower().replace(' ', '_')}.jpg"
                    ).save()
                    print(f" SubSubCategory created: {prod_type_name}")

    print("Category seeding complete!")

def seed_brands():
    brand_data = [
        {"name": "Nike", "description": "Global leader in sportswear.", "logo_path": "nike_logo.png"},
        {"name": "Adidas", "description": "Known for innovation and performance.", "logo_path": "adidas_logo.png"},
        {"name": "Puma", "description": "Performance and lifestyle brand.", "logo_path": "puma_logo.png"},
        {"name": "Reebok", "description": "Fitness and lifestyle brand.", "logo_path": "reebok_logo.png"},
        {"name": "Under Armour", "description": "Brand known for its performance gear.", "logo_path": "under_armour_logo.png"},
        {"name": "New Balance", "description": "Premium sports and lifestyle footwear.", "logo_path": "new_balance_logo.png"},
        {"name": "Asics", "description": "Japanese brand known for athletic shoes.", "logo_path": "asics_logo.png"},
        {"name": "Fila", "description": "Sporty, yet stylish apparel.", "logo_path": "fila_logo.png"},
        {"name": "Converse", "description": "Iconic American footwear brand.", "logo_path": "converse_logo.png"},
        {"name": "Vans", "description": "Skateboarding and streetwear culture.", "logo_path": "vans_logo.png"}
    ]

    if ProductBrands.objects.count() > 0:
        print("Brands already exist. Skipping brand seeding.")
        return

    for data in brand_data:
        brand = ProductBrands(
            name=data["name"],
            description=data["description"],
            logo_path=data["logo_path"]
        )
        brand.save()

    print("Brand seeding complete!")



def seed_data():
    seed_categories()
    seed_brands()
