# app/seed_data.py

from app.extensions import db
from app.models import Category, SubCategory, ProductType
from datetime import datetime

def seed_data():
    if Category.objects.count() == 0:
        print("🌱 Seeding categories, subcategories, product types...")

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
            "AUTOMOTIVE": ["Car Accessories", "Bike Accessories", "Tools"]
        }

        product_type_data = {
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

        # Create categories
        for cat_name, subcat_names in category_data.items():
            category = Category(
                name=cat_name,
                description=f"{cat_name} category description",
                img_url=f"/seed_images/categories/{cat_name.lower()}.jpg"
            )
            category.save()
            categories[cat_name] = category

            # Create subcategories for this category
            for subcat_name in subcat_names:
                subcategory = SubCategory(
                    name=subcat_name,
                    description=f"{subcat_name} subcategory description",
                    category=category,
                    img_url=f"/seed_images/subcategories/{subcat_name.lower().replace(' ', '_')}.jpg"
                )
                subcategory.save()
                subcategories[subcat_name] = subcategory

                # Create product types for this subcategory
                if subcat_name in product_type_data:
                    for prod_type_name in product_type_data[subcat_name]:
                        product_type = ProductType(
                            name=prod_type_name,
                            description=f"{prod_type_name} product type description",
                            category_id=category,
                            sub_category_id=subcategory,
                            img_url=f"/seed_images/product_types/{prod_type_name.lower().replace(' ', '_')}.jpg"
                        )
                        product_type.save()

        print("✅ Seeding complete!")

    else:
        print("⚠️ Categories already exist. Skipping seeding.")

