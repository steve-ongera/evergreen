# famers_website/management/commands/seed_products.py

import random
import uuid
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from farmers_website.models import Product, Category, SubCategory, Brand, Tag

class Command(BaseCommand):
    help = "Seed the database with at least 30 real agricultural products"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("🌱 Starting to seed products..."))

        product_data = [
            # Crops
            ("Fresh Maize (Green)", "Sweet and fresh green maize from local farms.", "kg", True),
            ("Dry Maize", "High quality dried maize, ideal for milling into flour.", "kg", False),
            ("Beans (Rosecoco)", "Nutritious and protein-rich rosecoco beans.", "kg", True),
            ("Sukumawiki (Kale)", "Fresh sukuma wiki rich in vitamins and minerals.", "kg", True),
            ("Tomatoes", "Ripe and juicy tomatoes perfect for salads and cooking.", "kg", True),
            ("Onions (Red)", "Strong-flavored red onions from Nyeri farms.", "kg", False),
            ("Cabbage", "Large, crisp cabbages ideal for home and commercial use.", "pc", True),
            ("Irish Potatoes", "Fresh potatoes from Kinangop highlands.", "kg", False),
            ("Sweet Potatoes", "Nutritious and naturally sweet potatoes.", "kg", True),
            # Livestock products
            ("Fresh Cow Milk", "Farm fresh, pasteurized cow milk.", "ltr", True),
            ("Eggs", "Farm-fresh eggs from free-range chickens.", "dozen", True),
            ("Broiler Chicken Meat", "Tender broiler chicken meat ready for cooking.", "kg", False),
            ("Tilapia Fish", "Fresh tilapia from aquaculture farms.", "kg", False),
            ("Goat Meat", "Lean and tasty goat meat from local farms.", "kg", False),
            ("Beef", "Premium beef cuts from grass-fed cattle.", "kg", False),
            # Fertilizers
            ("DAP Fertilizer", "Di-Ammonium Phosphate fertilizer for planting.", "bag", False),
            ("CAN Fertilizer", "Calcium Ammonium Nitrate for top dressing.", "bag", False),
            ("Organic Compost", "Rich organic compost for soil enrichment.", "bag", True),
            ("NPK Fertilizer", "Balanced NPK fertilizer for crops.", "bag", False),
            # Seeds
            ("Hybrid Maize Seeds", "High-yield hybrid maize seeds.", "bag", False),
            ("Kale Seeds", "Quality sukuma wiki seeds for planting.", "pack", True),
            ("Tomato Seeds", "High-germination tomato seeds.", "pack", True),
            ("Bean Seeds", "Certified bean seeds for planting.", "pack", False),
            # Equipment
            ("Knapsack Sprayer", "16L knapsack sprayer for pesticides and fertilizers.", "pc", False),
            ("Water Pump", "Petrol-powered water pump for irrigation.", "pc", False),
            ("Drip Irrigation Kit", "Complete drip irrigation system for small farms.", "box", False),
            ("Hand Hoe", "Durable hand hoe for farm work.", "pc", False),
            ("Wheelbarrow", "Heavy-duty wheelbarrow for farm transport.", "pc", False),
            ("Plastic Crates", "Strong plastic crates for harvesting and transport.", "pc", False),
        ]

        categories = list(Category.objects.all())
        subcategories = list(SubCategory.objects.all())
        brands = list(Brand.objects.all())
        tags = list(Tag.objects.all())

        if not categories or not brands or not tags:
            self.stdout.write(self.style.ERROR("⚠️ Please seed categories, brands, and tags first."))
            return

        created_count = 0
        for name, desc, unit, organic in product_data:
            # Random category/subcategory
            category = random.choice(categories)
            related_subs = [s for s in subcategories if s.category == category]
            subcategory = random.choice(related_subs) if related_subs else None

            # Random brand
            brand = random.choice(brands)

            # Random prices
            price = round(random.uniform(50, 2000), 2)
            discount_price = price - round(random.uniform(5, 100), 2) if random.choice([True, False]) else None
            cost_price = price - round(random.uniform(5, 50), 2)

            # Stock
            stock_quantity = random.randint(0, 200)

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "slug": slugify(name),
                    "sku": f"FARM-{uuid.uuid4().hex[:8].upper()}",
                    "description": desc,
                    "short_description": desc[:150],
                    "category": category,
                    "subcategory": subcategory,
                    "brand": brand,
                    "price": price,
                    "discount_price": discount_price,
                    "cost_price": cost_price,
                    "stock_quantity": stock_quantity,
                    "low_stock_threshold": 10,
                    "unit": unit,
                    "weight": round(random.uniform(0.5, 50.0), 2),
                    "is_active": True,
                    "is_featured": random.choice([True, False]),
                    "is_organic": organic,
                    "requires_prescription": False,
                    "meta_title": name,
                    "meta_description": f"Buy {name} - {desc}",
                    "meta_keywords": f"{name}, agriculture, Kenya, farm produce",
                    "harvest_date": date.today() - timedelta(days=random.randint(0, 60)),
                    "expiry_date": date.today() + timedelta(days=random.randint(10, 365)),
                    "origin": random.choice(["Nyeri", "Murang'a", "Kiambu", "Eldoret", "Nakuru", "Kisumu", "Makueni"])
                }
            )

            if created:
                created_count += 1
                # Assign random tags
                product.tags.set(random.sample(tags, random.randint(1, min(3, len(tags)))))
                self.stdout.write(self.style.SUCCESS(f"✅ Created product: {product.name}"))
            else:
                self.stdout.write(f"ℹ️ Product already exists: {product.name}")

        self.stdout.write(self.style.SUCCESS(f"\n🎯 Done! Created {created_count} new products."))
