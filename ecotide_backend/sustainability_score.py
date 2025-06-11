import pandas as pd
import numpy as np
import pickle
import os
import re
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import logging

logger = logging.getLogger(__name__)

class SustainabilityScorer:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.feature_keywords = None
        self.model_path = 'sustain_model.pkl'
        self.vectorizer_path = 'vectorizer.pkl'
        self.encoder_path = 'label_encoder.pkl'
        self.stats = {
            'total_predictions': 0,
            'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0},
            'categories_processed': set()
        }
        
        # Define sustainability keywords and features
        self.sustainability_keywords = {
            'excellent': ['organic', 'sustainable', 'eco-friendly', 'recycled', 'bamboo', 'hemp', 
                         'fair trade', 'carbon neutral', 'biodegradable', 'renewable', 'solar',
                         'wind power', 'upcycled', 'zero waste', 'compostable'],
            'good': ['recyclable', 'energy efficient', 'minimal packaging', 'local', 'natural',
                    'reusable', 'durable', 'long-lasting', 'refillable', 'plant-based'],
            'average': ['standard', 'conventional', 'regular', 'basic', 'economy'],
            'poor': ['disposable', 'single-use', 'plastic', 'non-recyclable', 'petroleum',
                    'synthetic', 'chemical', 'artificial', 'fast fashion', 'cheap'],
            'very_poor': ['toxic', 'harmful', 'wasteful', 'polluting', 'destructive',
                         'non-biodegradable', 'excessive packaging', 'planned obsolescence']
        }
        
        self.category_multipliers = {
            'electronics': 0.8,  # Generally less sustainable
            'clothing': 0.9,     # Fast fashion concerns
            'food': 1.1,         # Can be very sustainable
            'home': 1.0,         # Neutral
            'beauty': 0.95,      # Chemical concerns
            'toys': 0.85,        # Plastic/durability issues
            'books': 1.05,       # Generally sustainable
            'automotive': 0.7,   # High environmental impact
            'garden': 1.2,       # Often eco-friendly
            'health': 1.0        # Neutral
        }

    def load_or_train_model(self):
        """Load existing model or train a new one"""
        try:
            if (os.path.exists(self.model_path) and 
                os.path.exists(self.vectorizer_path) and 
                os.path.exists(self.encoder_path)):
                logger.info("Loading existing model...")
                self.load_model()
            else:
                logger.info("Training new model...")
                self.train_model()
        except Exception as e:
            logger.error(f"Error in load_or_train_model: {str(e)}")
            # Create a basic fallback model
            self.create_fallback_model()

    def load_model(self):
        """Load the trained model and associated components"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            with open(self.encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.create_fallback_model()

    def train_model(self):
        """Train a new sustainability scoring model"""
        try:
            # Load training data
            data_path = '../ecotide-ml/raw_products.csv'
            if not os.path.exists(data_path):
                logger.warning("Training data not found, creating synthetic data")
                self.create_synthetic_training_data(data_path)
            
            df = pd.read_csv(data_path)
            logger.info(f"Loaded {len(df)} training samples")
            
            # Prepare features
            X = self.prepare_features(df['product_title'].values)
            y = df['sustainability_grade'].values
            
            # Encode labels
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            
            # Fit vectorizer and transform text
            X_tfidf = self.vectorizer.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_tfidf, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
            )
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"Model accuracy: {accuracy:.3f}")
            
            # Save model
            self.save_model()
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            self.create_fallback_model()

    def create_synthetic_training_data(self, data_path):
        """Create synthetic training data for the model"""
        logger.info("Creating synthetic training data...")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Generate synthetic product data
        products = []
        
        # Excellent products (Grade A)
        excellent_products = [
            "Organic Bamboo Toothbrush - Biodegradable and Sustainable",
            "Solar Powered LED String Lights - Eco Friendly Garden Lighting",
            "Recycled Ocean Plastic Water Bottle - Zero Waste",
            "Organic Cotton Fair Trade T-Shirt - Sustainable Fashion",
            "Bamboo Fiber Yoga Mat - Eco-Friendly Exercise Equipment",
            "Compostable Phone Case - Biodegradable Protection",
            "Hemp Seed Oil Moisturizer - Natural Organic Skincare",
            "Upcycled Denim Tote Bag - Sustainable Shopping Bag",
            "Solar Battery Charger - Renewable Energy Power Bank",
            "Organic Beeswax Food Wraps - Zero Waste Kitchen"
        ]
        
        # Good products (Grade B)
        good_products = [
            "Stainless Steel Water Bottle - Reusable and Durable",
            "Energy Efficient LED Light Bulbs - Long Lasting",
            "Recycled Paper Notebook - Sustainable Office Supplies",
            "Natural Wool Sweater - Durable and Warm",
            "Refillable Ink Pen - Reduced Waste Writing",
            "Ceramic Travel Mug - Reusable Coffee Cup",
            "Wooden Kitchen Utensils - Natural and Durable",
            "Glass Food Storage Containers - Reusable Kitchen",
            "Cotton Canvas Sneakers - Durable Footwear",
            "Natural Loofah Sponge - Biodegradable Cleaning"
        ]
        
        # Average products (Grade C)
        average_products = [
            "Standard Cotton T-Shirt - Regular Fit",
            "Basic Plastic Storage Box - Household Organization",
            "Conventional Laundry Detergent - Standard Formula",
            "Regular Denim Jeans - Classic Fit",
            "Standard Ceramic Mug - Kitchen Drinkware",
            "Basic Polyester Pillow - Standard Comfort",
            "Regular Plastic Tupperware - Food Storage",
            "Standard Paper Towels - Household Cleaning",
            "Basic Acrylic Paint Set - Art Supplies",
            "Regular Synthetic Carpet - Home Flooring"
        ]
        
        # Poor products (Grade D)
        poor_products = [
            "Disposable Plastic Cups - Single Use Party Supplies",
            "Fast Fashion Polyester Dress - Trendy Clothing",
            "Plastic Disposable Razors - Single Use Shaving",
            "Synthetic Microfiber Cloth - Chemical Cleaning",
            "Plastic Shopping Bags - Disposable Grocery Bags",
            "Single Use Coffee Pods - Disposable K-Cups",
            "Plastic Food Containers - Disposable Packaging",
            "Synthetic Leather Jacket - Artificial Material",
            "Disposable Paper Plates - Single Use Dinnerware",
            "Plastic Cutlery Set - Disposable Utensils"
        ]
        
        # Very poor products (Grade E)
        very_poor_products = [
            "Toxic Paint Remover - Harmful Chemical Stripper",
            "Non-Recyclable Foam Packaging - Wasteful Shipping",
            "Planned Obsolescence Electronics - Short Lifespan Phone",
            "Excessive Plastic Packaging Toy - Wasteful Wrapping",
            "Chemical Pesticide Spray - Harmful Garden Treatment",
            "Non-Biodegradable Glitter - Environmental Pollutant",
            "Single Use Plastic Straws - Ocean Polluting Drinking",
            "Toxic Nail Polish - Harmful Chemical Beauty",
            "Fast Fashion Polyester Shirt - Polluting Clothing",
            "Disposable Electronic Vape - Wasteful Device"
        ]
        
        # Combine all products with grades
        for product in excellent_products:
            products.append({'product_title': product, 'sustainability_grade': 'A'})
        for product in good_products:
            products.append({'product_title': product, 'sustainability_grade': 'B'})
        for product in average_products:
            products.append({'product_title': product, 'sustainability_grade': 'C'})
        for product in poor_products:
            products.append({'product_title': product, 'sustainability_grade': 'D'})
        for product in very_poor_products:
            products.append({'product_title': product, 'sustainability_grade': 'E'})
        
        # Create DataFrame and save
        df = pd.DataFrame(products)
        df.to_csv(data_path, index=False)
        logger.info(f"Created synthetic training data with {len(df)} samples")

    def prepare_features(self, product_titles):
        """Prepare text features from product titles"""
        # Clean and preprocess titles
        cleaned_titles = []
        for title in product_titles:
            # Convert to lowercase and remove special characters
            cleaned = re.sub(r'[^a-zA-Z\s]', '', str(title).lower())
            cleaned_titles.append(cleaned)
        return cleaned_titles

    def create_fallback_model(self):
        """Create a simple rule-based fallback model"""
        logger.info("Creating fallback rule-based model")
        self.model = None  # Will use rule-based scoring
        self.vectorizer = None
        self.label_encoder = None

    def save_model(self):
        """Save the trained model and components"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            with open(self.encoder_path, 'wb') as f:
                pickle.dump(self.label_encoder, f)
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")

    def score_product(self, product_title, asin=''):
        """Score a product for sustainability"""
        try:
            self.stats['total_predictions'] += 1
            
            if self.model and self.vectorizer and self.label_encoder:
                # Use ML model
                grade = self._score_with_model(product_title)
            else:
                # Use rule-based scoring
                grade = self._score_with_rules(product_title)
            
            # Update stats
            self.stats['grade_distribution'][grade] += 1
            
            # Generate additional information
            result = {
                'grade': grade,
                'co2_impact': self._estimate_co2_impact(product_title, grade),
                'recyclable': self._assess_recyclability(product_title),
                'renewable_materials': self._assess_renewable_materials(product_title),
                'packaging_score': self._assess_packaging(product_title),
                'supply_chain_score': self._assess_supply_chain(product_title),
                'green_message': self._generate_green_message(product_title, grade),
                'confidence': self._calculate_confidence(product_title),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Scored product '{product_title[:30]}...' with grade {grade}")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring product: {str(e)}")
            return self._get_default_score()

    def _score_with_model(self, product_title):
        """Score using trained ML model"""
        try:
            # Prepare features
            features = self.prepare_features([product_title])
            X_tfidf = self.vectorizer.transform(features)
            
            # Predict
            prediction = self.model.predict(X_tfidf)[0]
            grade = self.label_encoder.inverse_transform([prediction])[0]
            
            return grade
        except Exception as e:
            logger.error(f"Error in ML scoring: {str(e)}")
            return self._score_with_rules(product_title)

    def _score_with_rules(self, product_title):
        """Score using rule-based approach"""
        title_lower = product_title.lower()
        score = 50  # Start with neutral score
        
        # Check for sustainability keywords
        for category, keywords in self.sustainability_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    if category == 'excellent':
                        score += 20
                    elif category == 'good':
                        score += 10
                    elif category == 'average':
                        score += 0
                    elif category == 'poor':
                        score -= 10
                    elif category == 'very_poor':
                        score -= 20
        
        # Apply category multipliers
        category = self._detect_category(title_lower)
        if category in self.category_multipliers:
            score *= self.category_multipliers[category]
        
        # Convert score to grade
        if score >= 80:
            return 'A'
        elif score >= 65:
            return 'B'
        elif score >= 45:
            return 'C'
        elif score >= 30:
            return 'D'
        else:
            return 'E'

    def _detect_category(self, title_lower):
        """Detect product category from title"""
        category_keywords = {
            'electronics': ['phone', 'laptop', 'computer', 'tablet', 'headphones', 'speaker', 'tv', 'camera'],
            'clothing': ['shirt', 't-shirt', 'dress', 'pants', 'jeans', 'jacket', 'shoes', 'sneakers', 'sweater'],
            'food': ['organic', 'snack', 'coffee', 'tea', 'chocolate', 'nuts', 'supplement', 'vitamin'],
            'home': ['furniture', 'chair', 'table', 'lamp', 'decor', 'pillow', 'blanket', 'storage'],
            'beauty': ['moisturizer', 'shampoo', 'soap', 'lotion', 'cream', 'oil', 'cosmetic', 'perfume'],
            'toys': ['toy', 'game', 'puzzle', 'doll', 'action figure', 'board game', 'educational'],
            'books': ['book', 'novel', 'textbook', 'journal', 'notebook', 'diary', 'manual'],
            'automotive': ['car', 'auto', 'vehicle', 'tire', 'oil', 'brake', 'engine', 'battery'],
            'garden': ['plant', 'seed', 'fertilizer', 'tool', 'garden', 'lawn', 'outdoor', 'solar'],
            'health': ['medical', 'health', 'fitness', 'exercise', 'yoga', 'protein', 'supplement']
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    self.stats['categories_processed'].add(category)
                    return category
        return 'other'

    def _estimate_co2_impact(self, product_title, grade):
        """Estimate CO2 impact based on product and grade"""
        base_impact = {
            'A': 1.2,  # kg CO2
            'B': 2.5,
            'C': 4.8,
            'D': 8.1,
            'E': 12.5
        }
        
        category = self._detect_category(product_title.lower())
        category_multipliers = {
            'electronics': 3.0,
            'automotive': 5.0,
            'clothing': 1.5,
            'food': 0.8,
            'home': 2.0,
            'beauty': 1.2,
            'toys': 1.8,
            'books': 0.5,
            'garden': 0.9,
            'health': 1.1
        }
        
        impact = base_impact[grade] * category_multipliers.get(category, 1.0)
        return f"{impact:.1f} kg CO₂"

    def _assess_recyclability(self, product_title):
        """Assess if product is recyclable"""
        title_lower = product_title.lower()
        recyclable_keywords = ['metal', 'aluminum', 'steel', 'glass', 'paper', 'cardboard', 'recyclable']
        non_recyclable_keywords = ['composite', 'mixed materials', 'laminated', 'foam']
        
        for keyword in recyclable_keywords:
            if keyword in title_lower:
                return True
        
        for keyword in non_recyclable_keywords:
            if keyword in title_lower:
                return False
        
        # Default based on category
        category = self._detect_category(title_lower)
        recyclable_categories = ['electronics', 'books', 'home']
        return category in recyclable_categories

    def _assess_renewable_materials(self, product_title):
        """Assess if product uses renewable materials"""
        title_lower = product_title.lower()
        renewable_keywords = ['bamboo', 'hemp', 'organic cotton', 'wood', 'cork', 'renewable', 'bio-based']
        
        for keyword in renewable_keywords:
            if keyword in title_lower:
                return True
        return False

    def _assess_packaging(self, product_title):
        """Assess packaging sustainability"""
        title_lower = product_title.lower()
        
        if any(word in title_lower for word in ['minimal packaging', 'plastic-free', 'zero waste']):
            return 'Excellent'
        elif any(word in title_lower for word in ['recyclable packaging', 'cardboard']):
            return 'Good'
        elif any(word in title_lower for word in ['excessive packaging', 'plastic packaging']):
            return 'Poor'
        else:
            return 'Average'

    def _assess_supply_chain(self, product_title):
        """Assess supply chain sustainability"""
        title_lower = product_title.lower()
        
        if any(word in title_lower for word in ['local', 'fair trade', 'ethical', 'local sourced']):
            return 'Excellent'
        elif any(word in title_lower for word in ['certified', 'responsible']):
            return 'Good'
        else:
            return 'Unknown'

    def _generate_green_message(self, product_title, grade):
        """Generate contextual green message"""
        title_lower = product_title.lower()
        category = self._detect_category(title_lower)
        
        messages = {
            'A': [
                "Excellent choice! This product supports sustainable practices.",
                "Great pick! This item has minimal environmental impact.",
                "Perfect! This product promotes a circular economy."
            ],
            'B': [
                "Good choice! This product is more sustainable than average.",
                "Nice pick! Consider reusing or recycling when done.",
                "Well done! This item has better environmental credentials."
            ],
            'C': [
                "Average sustainability. Look for eco-friendly alternatives.",
                "Consider checking for more sustainable options.",
                "This product meets basic environmental standards."
            ],
            'D': [
                "Below average sustainability. Consider alternatives.",
                "Look for products with better environmental ratings.",
                "This item could have significant environmental impact."
            ],
            'E': [
                "Poor sustainability rating. Strongly consider alternatives.",
                "This product may have high environmental impact.",
                "Look for eco-friendly alternatives to reduce your footprint."
            ]
        }
        
        import random
        return random.choice(messages.get(grade, messages['C']))

    def _calculate_confidence(self, product_title):
        """Calculate confidence score for the prediction"""
        title_lower = product_title.lower()
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have clear sustainability indicators
        total_keywords = sum(len(keywords) for keywords in self.sustainability_keywords.values())
        matching_keywords = 0
        
        for keywords in self.sustainability_keywords.values():
            for keyword in keywords:
                if keyword in title_lower:
                    matching_keywords += 1
        
        keyword_confidence = min(matching_keywords / 5, 0.4)  # Max 0.4 from keywords
        confidence += keyword_confidence
        
        # Add confidence based on title length and detail
        if len(product_title.split()) >= 4:
            confidence += 0.1
        
        return min(confidence, 0.95)  # Cap at 95%

    def _get_default_score(self):
        """Return default score when scoring fails"""
        return {
            'grade': 'C',
            'co2_impact': 'Unknown',
            'recyclable': False,
            'renewable_materials': False,
            'packaging_score': 'Unknown',
            'supply_chain_score': 'Unknown',
            'green_message': 'Unable to assess sustainability. Please try again.',
            'confidence': 0.1,
            'timestamp': datetime.now().isoformat()
        }

    def get_suggestions(self, product_title, category=''):
        """Get sustainable product suggestions"""
        # This is a simplified version - in reality, you'd query a database
        # or use a recommendation system
        suggestions = [
            {
                'title': 'Eco-friendly alternative suggestion',
                'grade': 'A',
                'reason': 'Made from sustainable materials',
                'url': '#'
            }
        ]
        return suggestions

    def get_stats(self):
        """Get API usage statistics"""
        return {
            'total_predictions': self.stats['total_predictions'],
            'grade_distribution': dict(self.stats['grade_distribution']),
            'categories_processed': list(self.stats['categories_processed']),
            'model_type': 'ML' if self.model else 'Rule-based',
            'last_updated': datetime.now().isoformat()
        }

    def get_supported_categories(self):
        """Get list of supported product categories"""
        return list(self.category_multipliers.keys())
