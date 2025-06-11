#!/usr/bin/env python3
"""
EcoTide Data Processing Module

This module handles data loading, cleaning, and preprocessing for the
sustainability scoring machine learning model.
"""

import os
import re
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Handles data processing for sustainability scoring model
    """
    
    def __init__(self):
        # Sustainability keyword categories for feature engineering
        self.sustainability_keywords = {
            'excellent': [
                'organic', 'sustainable', 'eco-friendly', 'recycled', 'bamboo', 'hemp',
                'fair trade', 'carbon neutral', 'biodegradable', 'renewable', 'solar',
                'wind power', 'upcycled', 'zero waste', 'compostable', 'cruelty-free',
                'vegan', 'plant-based', 'bio-based', 'post-consumer', 'fsc certified'
            ],
            'good': [
                'recyclable', 'energy efficient', 'minimal packaging', 'local', 'natural',
                'reusable', 'durable', 'long-lasting', 'refillable', 'glass', 'wood',
                'cotton', 'wool', 'linen', 'cork', 'ceramic', 'steel', 'aluminum'
            ],
            'average': [
                'standard', 'conventional', 'regular', 'basic', 'economy', 'traditional',
                'classic', 'normal', 'typical', 'ordinary'
            ],
            'poor': [
                'disposable', 'single-use', 'plastic', 'non-recyclable', 'petroleum',
                'synthetic', 'chemical', 'artificial', 'fast fashion', 'cheap',
                'polyester', 'nylon', 'acrylic', 'polystyrene', 'pvc'
            ],
            'very_poor': [
                'toxic', 'harmful', 'wasteful', 'polluting', 'destructive',
                'non-biodegradable', 'excessive packaging', 'planned obsolescence',
                'microplastics', 'formaldehyde', 'lead', 'mercury', 'benzene'
            ]
        }
        
        # Product categories and their sustainability characteristics
        self.category_patterns = {
            'electronics': {
                'keywords': ['phone', 'laptop', 'computer', 'tablet', 'headphones', 'speaker', 
                           'tv', 'camera', 'smartwatch', 'charger', 'cable', 'mouse', 'keyboard'],
                'sustainability_factors': ['energy efficiency', 'durability', 'repairability', 'recycling']
            },
            'clothing': {
                'keywords': ['shirt', 't-shirt', 'dress', 'pants', 'jeans', 'jacket', 'shoes', 
                           'sneakers', 'sweater', 'coat', 'hat', 'socks', 'underwear'],
                'sustainability_factors': ['material source', 'production methods', 'durability', 'fair labor']
            },
            'food': {
                'keywords': ['organic', 'snack', 'coffee', 'tea', 'chocolate', 'nuts', 'supplement', 
                           'vitamin', 'protein', 'cereal', 'juice', 'water', 'wine'],
                'sustainability_factors': ['organic certification', 'packaging', 'local sourcing', 'fair trade']
            },
            'home': {
                'keywords': ['furniture', 'chair', 'table', 'lamp', 'decor', 'pillow', 'blanket', 
                           'storage', 'mirror', 'curtain', 'rug', 'shelf', 'frame'],
                'sustainability_factors': ['material sustainability', 'durability', 'minimal packaging']
            },
            'beauty': {
                'keywords': ['moisturizer', 'shampoo', 'soap', 'lotion', 'cream', 'oil', 'cosmetic', 
                           'perfume', 'makeup', 'serum', 'cleanser', 'sunscreen'],
                'sustainability_factors': ['natural ingredients', 'cruelty-free', 'packaging', 'refillable']
            },
            'toys': {
                'keywords': ['toy', 'game', 'puzzle', 'doll', 'action figure', 'board game', 
                           'educational', 'block', 'stuffed animal', 'ball'],
                'sustainability_factors': ['material safety', 'durability', 'educational value', 'minimal packaging']
            },
            'books': {
                'keywords': ['book', 'novel', 'textbook', 'journal', 'notebook', 'diary', 'manual', 
                           'magazine', 'comic', 'ebook', 'audiobook'],
                'sustainability_factors': ['recycled paper', 'digital format', 'durability', 'educational value']
            },
            'automotive': {
                'keywords': ['car', 'auto', 'vehicle', 'tire', 'oil', 'brake', 'engine', 'battery', 
                           'fuel', 'motor', 'transmission', 'electric'],
                'sustainability_factors': ['fuel efficiency', 'electric', 'durability', 'recyclability']
            },
            'garden': {
                'keywords': ['plant', 'seed', 'fertilizer', 'tool', 'garden', 'lawn', 'outdoor', 
                           'solar', 'pot', 'soil', 'mulch', 'pesticide'],
                'sustainability_factors': ['organic methods', 'water efficiency', 'native plants', 'solar power']
            },
            'health': {
                'keywords': ['medical', 'health', 'fitness', 'exercise', 'yoga', 'protein', 
                           'supplement', 'vitamin', 'medicine', 'bandage', 'thermometer'],
                'sustainability_factors': ['natural ingredients', 'minimal packaging', 'durability', 'safety']
            }
        }

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process raw product data for training
        
        Args:
            df: Raw product dataframe
            
        Returns:
            Processed dataframe ready for training
        """
        logger.info("Processing product data...")
        
        try:
            # Make a copy to avoid modifying original
            processed_df = df.copy()
            
            # Clean product titles
            processed_df['product_title'] = processed_df['product_title'].apply(self._clean_title)
            
            # Extract features
            processed_df = self._extract_features(processed_df)
            
            # Validate and clean sustainability grades
            processed_df = self._validate_grades(processed_df)
            
            # Remove duplicates
            initial_count = len(processed_df)
            processed_df = processed_df.drop_duplicates(subset=['product_title'])
            final_count = len(processed_df)
            
            if initial_count != final_count:
                logger.info(f"Removed {initial_count - final_count} duplicate products")
            
            # Filter out products with insufficient information
            processed_df = processed_df[processed_df['product_title'].str.len() >= 10]
            
            logger.info(f"Processed {len(processed_df)} products successfully")
            return processed_df
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            raise

    def _clean_title(self, title: str) -> str:
        """Clean and normalize product titles"""
        if pd.isna(title):
            return ""
        
        # Convert to string and lowercase
        title = str(title).lower().strip()
        
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title)
        
        # Remove special characters but keep important ones
        title = re.sub(r'[^\w\s\-\+\&\%]', ' ', title)
        
        # Remove common noise words that don't add value
        noise_words = ['new', 'hot', 'sale', 'deal', 'offer', 'discount', 'free shipping',
                      'best seller', 'top rated', 'amazon choice', 'limited time']
        
        for noise in noise_words:
            title = title.replace(noise, ' ')
        
        # Clean up extra spaces again
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title

    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract additional features from product data"""
        logger.info("Extracting features from product data...")
        
        # Category detection
        df['category'] = df['product_title'].apply(self._detect_category)
        
        # Sustainability keyword counts
        for category, keywords in self.sustainability_keywords.items():
            df[f'{category}_keywords'] = df['product_title'].apply(
                lambda x: sum(1 for keyword in keywords if keyword in x)
            )
        
        # Title length and word count
        df['title_length'] = df['product_title'].str.len()
        df['word_count'] = df['product_title'].str.split().str.len()
        
        # Brand detection (simple heuristic)
        df['has_brand'] = df['product_title'].apply(self._detect_brand)
        
        # Price-related keywords
        price_keywords = ['premium', 'luxury', 'budget', 'affordable', 'cheap', 'expensive']
        df['price_keywords'] = df['product_title'].apply(
            lambda x: sum(1 for keyword in price_keywords if keyword in x)
        )
        
        return df

    def _detect_category(self, title: str) -> str:
        """Detect product category from title"""
        title_lower = title.lower()
        
        for category, info in self.category_patterns.items():
            for keyword in info['keywords']:
                if keyword in title_lower:
                    return category
        
        return 'other'

    def _detect_brand(self, title: str) -> bool:
        """Simple brand detection heuristic"""
        # Look for capitalized words at the beginning
        words = title.split()
        if not words:
            return False
        
        # Common brand indicators
        brand_indicators = ['by', 'from', 'brand:', 'tm', '®', '©']
        for indicator in brand_indicators:
            if indicator in title.lower():
                return True
        
        # Check if first word looks like a brand (capitalized)
        return len(words[0]) > 2 and words[0].istitle()

    def _validate_grades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean sustainability grades"""
        valid_grades = {'A', 'B', 'C', 'D', 'E'}
        
        # Convert grades to uppercase
        df['sustainability_grade'] = df['sustainability_grade'].str.upper()
        
        # Filter valid grades
        valid_mask = df['sustainability_grade'].isin(valid_grades)
        invalid_count = (~valid_mask).sum()
        
        if invalid_count > 0:
            logger.warning(f"Filtering out {invalid_count} products with invalid grades")
            df = df[valid_mask]
        
        return df

    def create_training_data(self, output_path: str, num_samples: int = 1000):
        """
        Create comprehensive training data for the sustainability model
        
        Args:
            output_path: Path to save the training data CSV
            num_samples: Number of samples to generate
        """
        logger.info(f"Creating training data with {num_samples} samples...")
        
        try:
            products = []
            
            # Define product templates for each grade
            grade_templates = {
                'A': self._get_excellent_products(),
                'B': self._get_good_products(),
                'C': self._get_average_products(),
                'D': self._get_poor_products(),
                'E': self._get_very_poor_products()
            }
            
            # Generate balanced dataset
            samples_per_grade = num_samples // 5
            
            for grade, templates in grade_templates.items():
                for i in range(samples_per_grade):
                    # Select template and add variations
                    template = templates[i % len(templates)]
                    
                    # Add some variation to the template
                    varied_product = self._add_product_variation(template, grade)
                    
                    products.append({
                        'product_title': varied_product,
                        'sustainability_grade': grade,
                        'created_date': datetime.now().isoformat()
                    })
            
            # Create DataFrame and save
            df = pd.DataFrame(products)
            
            # Shuffle the data
            df = df.sample(frac=1, random_state=42).reset_index(drop=True)
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to CSV
            df.to_csv(output_path, index=False)
            logger.info(f"Training data saved to {output_path}")
            
            # Log statistics
            grade_counts = df['sustainability_grade'].value_counts()
            logger.info(f"Grade distribution: {grade_counts.to_dict()}")
            
        except Exception as e:
            logger.error(f"Error creating training data: {str(e)}")
            raise

    def _get_excellent_products(self) -> List[str]:
        """Get excellent sustainability products (Grade A)"""
        return [
            "Organic Bamboo Toothbrush - Biodegradable and Sustainable",
            "Solar Powered LED String Lights - Eco Friendly Garden Lighting",
            "Recycled Ocean Plastic Water Bottle - Zero Waste BPA Free",
            "Organic Cotton Fair Trade T-Shirt - Sustainable Fashion",
            "Bamboo Fiber Yoga Mat - Eco-Friendly Exercise Equipment",
            "Compostable Phone Case - Biodegradable Protection",
            "Hemp Seed Oil Moisturizer - Natural Organic Skincare",
            "Upcycled Denim Tote Bag - Sustainable Shopping Bag",
            "Solar Battery Charger - Renewable Energy Power Bank",
            "Organic Beeswax Food Wraps - Zero Waste Kitchen",
            "FSC Certified Wooden Cutting Board - Sustainable Kitchen",
            "Organic Hemp Backpack - Eco Friendly Travel Bag",
            "Solar Garden Stake Lights - Renewable Outdoor Lighting",
            "Recycled Aluminum Water Bottle - Sustainable Hydration",
            "Organic Cotton Bed Sheets - Fair Trade Bedding",
            "Bamboo Smartphone Stand - Eco Friendly Tech Accessory",
            "Compostable Coffee Pods - Zero Waste Brewing",
            "Organic Shampoo Bar - Plastic Free Hair Care",
            "Upcycled Tire Planter - Sustainable Garden Container",
            "Solar Powered Radio - Renewable Energy Entertainment"
        ]

    def _get_good_products(self) -> List[str]:
        """Get good sustainability products (Grade B)"""
        return [
            "Stainless Steel Water Bottle - Reusable and Durable",
            "Energy Efficient LED Light Bulbs - Long Lasting 25000 Hours",
            "Recycled Paper Notebook - Sustainable Office Supplies",
            "Natural Wool Sweater - Durable and Warm Winter Clothing",
            "Refillable Ink Pen - Reduced Waste Writing Instrument",
            "Ceramic Travel Mug - Reusable Coffee Cup with Lid",
            "Wooden Kitchen Utensils Set - Natural and Durable Cooking",
            "Glass Food Storage Containers - Reusable Kitchen Organization",
            "Cotton Canvas Sneakers - Durable Breathable Footwear",
            "Natural Loofah Sponge - Biodegradable Cleaning Tool",
            "Cork Yoga Block - Natural Exercise Equipment",
            "Linen Tea Towels - Natural Kitchen Textiles",
            "Wool Dryer Balls - Reusable Fabric Softener",
            "Ceramic Dinner Plates - Durable Dishware Set",
            "Natural Jute Rug - Sustainable Floor Covering",
            "Wooden Picture Frame - Natural Home Decor",
            "Cotton Mesh Produce Bags - Reusable Shopping",
            "Glass Mason Jars - Multipurpose Storage Containers",
            "Natural Bristle Cleaning Brush - Biodegradable Tool",
            "Linen Curtains - Natural Window Treatment"
        ]

    def _get_average_products(self) -> List[str]:
        """Get average sustainability products (Grade C)"""
        return [
            "Standard Cotton T-Shirt - Regular Fit Basic Tee",
            "Basic Plastic Storage Box - Household Organization Container",
            "Conventional Laundry Detergent - Standard Formula Cleaning",
            "Regular Denim Jeans - Classic Fit Casual Pants",
            "Standard Ceramic Mug - Kitchen Drinkware 12oz",
            "Basic Polyester Pillow - Standard Comfort Sleep",
            "Regular Plastic Tupperware - Food Storage Container Set",
            "Standard Paper Towels - Household Cleaning Supplies",
            "Basic Acrylic Paint Set - Art Supplies for Beginners",
            "Regular Synthetic Carpet - Home Flooring 12x9 feet",
            "Standard Office Chair - Basic Ergonomic Seating",
            "Regular Plastic Hangers - Closet Organization 20 Pack",
            "Basic Polyester Blanket - Standard Throw Cover",
            "Standard Aluminum Foil - Kitchen Cooking Supplies",
            "Regular Glass Drinking Glasses - Basic Drinkware Set",
            "Basic Cotton Socks - Standard Comfort Footwear",
            "Standard Plastic Trash Bags - Household Waste Management",
            "Regular Paper Plates - Disposable Party Supplies",
            "Basic Shower Curtain - Standard Bathroom Accessory",
            "Standard Pencil Set - Basic Writing Supplies"
        ]

    def _get_poor_products(self) -> List[str]:
        """Get poor sustainability products (Grade D)"""
        return [
            "Disposable Plastic Cups - Single Use Party Supplies 50 Pack",
            "Fast Fashion Polyester Dress - Trendy Seasonal Clothing",
            "Plastic Disposable Razors - Single Use Shaving 10 Pack",
            "Synthetic Microfiber Cloth - Chemical Treated Cleaning",
            "Plastic Shopping Bags - Disposable Grocery Carrier 100 Pack",
            "Single Use Coffee Pods - Disposable K-Cup Compatible 48 Count",
            "Plastic Food Containers - Disposable Takeout Packaging",
            "Synthetic Leather Jacket - Artificial PVC Material",
            "Disposable Paper Plates - Single Use Dinnerware 100 Pack",
            "Plastic Cutlery Set - Disposable Utensils Party Pack",
            "Synthetic Carpet Tiles - Chemical Treated Flooring",
            "Plastic Wrap - Single Use Food Storage Film",
            "Disposable Plastic Tablecloth - Single Use Party Decor",
            "Synthetic Fill Comforter - Chemical Treated Bedding",
            "Plastic Disposable Containers - Single Use Storage",
            "Synthetic Fabric Softener - Chemical Laundry Treatment",
            "Plastic Disposable Gloves - Single Use Protection 100 Pack",
            "Synthetic Air Freshener - Chemical Room Spray",
            "Disposable Aluminum Pans - Single Use Cooking",
            "Plastic Disposable Water Bottles - Single Use 24 Pack"
        ]

    def _get_very_poor_products(self) -> List[str]:
        """Get very poor sustainability products (Grade E)"""
        return [
            "Toxic Paint Remover - Harmful Chemical Stripper with Benzene",
            "Non-Recyclable Foam Packaging - Wasteful Shipping Polystyrene",
            "Planned Obsolescence Smartphone - 6 Month Lifespan Design",
            "Excessive Plastic Packaging Toy - Triple Wrapped Wasteful",
            "Chemical Pesticide Spray - Harmful Garden Treatment with Toxins",
            "Non-Biodegradable Glitter - Environmental Pollutant Microplastic",
            "Single Use Plastic Straws - Ocean Polluting Drinking 500 Pack",
            "Toxic Nail Polish - Harmful Chemical Beauty with Formaldehyde",
            "Fast Fashion Polyester Shirt - Polluting Sweatshop Clothing",
            "Disposable Electronic Vape - Wasteful Lithium Battery Device",
            "Lead Paint - Toxic Home Decoration with Heavy Metals",
            "Mercury Thermometer - Harmful Medical Device",
            "Asbestos Insulation - Dangerous Building Material",
            "Chemical Drain Cleaner - Toxic Pipe Treatment with Acids",
            "Non-Recyclable Electronics - Planned Obsolescence Tablet",
            "Toxic Cleaning Spray - Harmful Household Chemical with VOCs",
            "Single Use Plastic Bags - Ocean Destroying Shopping 1000 Pack",
            "Chemical Fertilizer - Harmful Synthetic Lawn Treatment",
            "Disposable Fashion Jewelry - Toxic Metal Costume Accessories",
            "Wasteful Packaging Product - 10x Oversized Box for Small Item"
        ]

    def _add_product_variation(self, template: str, grade: str) -> str:
        """Add variation to product templates"""
        variations = {
            'A': ['eco-friendly', 'sustainable', 'green', 'natural', 'organic'],
            'B': ['durable', 'quality', 'reliable', 'long-lasting', 'efficient'],
            'C': ['standard', 'basic', 'regular', 'classic', 'traditional'],
            'D': ['cheap', 'budget', 'economy', 'disposable', 'convenient'],
            'E': ['toxic', 'harmful', 'wasteful', 'polluting', 'dangerous']
        }
        
        # Randomly add variation words (30% chance)
        import random
        if random.random() < 0.3:
            variation_word = random.choice(variations[grade])
            # Insert the variation word randomly in the title
            words = template.split()
            insert_pos = random.randint(0, len(words))
            words.insert(insert_pos, variation_word)
            return ' '.join(words)
        
        return template

    def load_external_data(self, source_url: str) -> pd.DataFrame:
        """
        Load product data from external sources
        
        Args:
            source_url: URL to product data
            
        Returns:
            DataFrame with product data
        """
        logger.info(f"Loading data from external source: {source_url}")
        
        try:
            # This is a placeholder for loading real data from APIs or databases
            # In a real implementation, you might load from:
            # - E-commerce APIs (Amazon, eBay, etc.)
            # - Sustainability databases
            # - Product catalogs
            
            response = requests.get(source_url, timeout=30)
            response.raise_for_status()
            
            # Parse the response based on content type
            if 'json' in response.headers.get('content-type', ''):
                data = response.json()
                df = pd.DataFrame(data)
            else:
                # Assume CSV format
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
            
            logger.info(f"Loaded {len(df)} products from external source")
            return df
            
        except Exception as e:
            logger.error(f"Error loading external data: {str(e)}")
            raise

    def augment_data(self, df: pd.DataFrame, augmentation_factor: float = 1.5) -> pd.DataFrame:
        """
        Augment existing data to increase training set size
        
        Args:
            df: Original dataframe
            augmentation_factor: Multiplier for data size
            
        Returns:
            Augmented dataframe
        """
        logger.info(f"Augmenting data with factor {augmentation_factor}")
        
        try:
            original_size = len(df)
            target_size = int(original_size * augmentation_factor)
            additional_samples = target_size - original_size
            
            augmented_samples = []
            
            for _ in range(additional_samples):
                # Select random sample to augment
                sample = df.sample(1).iloc[0]
                
                # Create augmented version
                augmented_title = self._augment_title(sample['product_title'])
                
                augmented_samples.append({
                    'product_title': augmented_title,
                    'sustainability_grade': sample['sustainability_grade']
                })
            
            # Combine original and augmented data
            augmented_df = pd.concat([df, pd.DataFrame(augmented_samples)], ignore_index=True)
            
            logger.info(f"Augmented data from {original_size} to {len(augmented_df)} samples")
            return augmented_df
            
        except Exception as e:
            logger.error(f"Error augmenting data: {str(e)}")
            raise

    def _augment_title(self, title: str) -> str:
        """Augment a product title with variations"""
        import random
        
        words = title.split()
        
        # Random operations
        operations = [
            lambda w: w,  # Keep original
            lambda w: self._add_synonym(w),  # Add synonym
            lambda w: self._reorder_words(w),  # Reorder words
            lambda w: self._add_descriptive_word(w),  # Add descriptive word
        ]
        
        operation = random.choice(operations)
        return operation(words)

    def _add_synonym(self, words: List[str]) -> str:
        """Add synonyms to words"""
        synonyms = {
            'organic': ['natural', 'bio', 'ecological'],
            'sustainable': ['eco-friendly', 'green', 'environmentally friendly'],
            'recyclable': ['reusable', 'renewable', 'recoverable'],
            'biodegradable': ['compostable', 'decomposable', 'natural'],
            'durable': ['long-lasting', 'sturdy', 'robust'],
            'efficient': ['effective', 'optimal', 'smart']
        }
        
        import random
        new_words = []
        for word in words:
            if word in synonyms and random.random() < 0.3:
                new_words.append(random.choice(synonyms[word]))
            else:
                new_words.append(word)
        
        return ' '.join(new_words)

    def _reorder_words(self, words: List[str]) -> str:
        """Randomly reorder words while maintaining meaning"""
        import random
        
        if len(words) <= 2:
            return ' '.join(words)
        
        # Keep first and last words in place, shuffle middle
        if len(words) > 4:
            middle = words[1:-1]
            random.shuffle(middle)
            return ' '.join([words[0]] + middle + [words[-1]])
        
        return ' '.join(words)

    def _add_descriptive_word(self, words: List[str]) -> str:
        """Add descriptive words to enhance title"""
        import random
        
        descriptive_words = [
            'premium', 'professional', 'high-quality', 'deluxe', 'advanced',
            'improved', 'enhanced', 'superior', 'ultimate', 'perfect'
        ]
        
        if random.random() < 0.3:
            word = random.choice(descriptive_words)
            pos = random.randint(0, len(words))
            words.insert(pos, word)
        
        return ' '.join(words)
