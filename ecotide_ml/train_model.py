#!/usr/bin/env python3
"""
EcoTide ML Model Training Script

This script trains a machine learning model to predict sustainability scores
for e-commerce products based on their titles and descriptions.
"""

import os
import sys
import pickle
import logging
import argparse
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

from data_processor import DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SustainabilityModelTrainer:
    """
    Trains and evaluates a machine learning model for sustainability scoring
    """
    
    def __init__(self, data_path='raw_products.csv', output_dir='../ecotide-backend'):
        self.data_path = data_path
        self.output_dir = output_dir
        self.processor = DataProcessor()
        
        # Model components
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.feature_names = None
        
        # Training data
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
        # Model paths
        self.model_path = os.path.join(output_dir, 'sustain_model.pkl')
        self.vectorizer_path = os.path.join(output_dir, 'vectorizer.pkl')
        self.encoder_path = os.path.join(output_dir, 'label_encoder.pkl')
        self.metadata_path = os.path.join(output_dir, 'model_metadata.pkl')

    def load_and_prepare_data(self):
        """Load and prepare training data"""
        logger.info("Loading and preparing training data...")
        
        try:
            # Load raw data
            if not os.path.exists(self.data_path):
                logger.warning(f"Data file {self.data_path} not found. Creating sample data...")
                self.processor.create_training_data(self.data_path)
            
            # Load the dataset
            df = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(df)} samples from {self.data_path}")
            
            # Process the data
            df_processed = self.processor.process_data(df)
            logger.info(f"Processed data shape: {df_processed.shape}")
            
            # Check for required columns
            required_columns = ['product_title', 'sustainability_grade']
            missing_columns = [col for col in required_columns if col not in df_processed.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Prepare features and targets
            X = df_processed['product_title'].values
            y = df_processed['sustainability_grade'].values
            
            # Validate grades
            valid_grades = {'A', 'B', 'C', 'D', 'E'}
            invalid_grades = set(y) - valid_grades
            if invalid_grades:
                logger.warning(f"Found invalid grades: {invalid_grades}. Filtering them out...")
                valid_mask = np.isin(y, list(valid_grades))
                X = X[valid_mask]
                y = y[valid_mask]
            
            logger.info(f"Final dataset: {len(X)} samples")
            logger.info(f"Grade distribution: {pd.Series(y).value_counts().to_dict()}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def create_features(self, X):
        """Create TF-IDF features from product titles"""
        logger.info("Creating TF-IDF features...")
        
        try:
            # Initialize vectorizer with optimized parameters
            self.vectorizer = TfidfVectorizer(
                max_features=2000,  # Increased for better feature coverage
                stop_words='english',
                ngram_range=(1, 3),  # Include trigrams for better context
                lowercase=True,
                min_df=2,  # Ignore terms that appear in less than 2 documents
                max_df=0.95,  # Ignore terms that appear in more than 95% of documents
                sublinear_tf=True,  # Apply sublinear tf scaling
                norm='l2'  # L2 normalization
            )
            
            # Fit and transform the text data
            X_tfidf = self.vectorizer.fit_transform(X)
            
            # Store feature names for analysis
            self.feature_names = self.vectorizer.get_feature_names_out()
            
            logger.info(f"Created {X_tfidf.shape[1]} TF-IDF features")
            logger.info(f"Feature matrix shape: {X_tfidf.shape}")
            logger.info(f"Feature matrix sparsity: {1.0 - X_tfidf.nnz / np.prod(X_tfidf.shape):.3f}")
            
            return X_tfidf
            
        except Exception as e:
            logger.error(f"Error creating features: {str(e)}")
            raise

    def encode_labels(self, y):
        """Encode sustainability grades to numeric labels"""
        logger.info("Encoding labels...")
        
        try:
            # Create label encoder with explicit ordering
            self.label_encoder = LabelEncoder()
            
            # Fit the encoder
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Log the mapping
            classes = self.label_encoder.classes_
            logger.info(f"Label encoding: {dict(zip(classes, range(len(classes))))}")
            
            return y_encoded
            
        except Exception as e:
            logger.error(f"Error encoding labels: {str(e)}")
            raise

    def split_data(self, X, y, test_size=0.2, random_state=42):
        """Split data into training and testing sets"""
        logger.info(f"Splitting data (test_size={test_size})...")
        
        try:
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, 
                test_size=test_size, 
                random_state=random_state, 
                stratify=y  # Maintain class distribution
            )
            
            logger.info(f"Training set: {self.X_train.shape[0]} samples")
            logger.info(f"Test set: {self.X_test.shape[0]} samples")
            
            # Log class distributions
            train_dist = pd.Series(self.y_train).value_counts().to_dict()
            test_dist = pd.Series(self.y_test).value_counts().to_dict()
            logger.info(f"Training distribution: {train_dist}")
            logger.info(f"Test distribution: {test_dist}")
            
        except Exception as e:
            logger.error(f"Error splitting data: {str(e)}")
            raise

    def train_model(self, hyperparameter_tuning=False):
        """Train the sustainability scoring model"""
        logger.info("Training sustainability scoring model...")
        
        try:
            if hyperparameter_tuning:
                logger.info("Performing hyperparameter tuning...")
                self._train_with_grid_search()
            else:
                logger.info("Training with default parameters...")
                self._train_default_model()
            
            # Evaluate the model
            self.evaluate_model()
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def _train_default_model(self):
        """Train model with default parameters"""
        self.model = RandomForestClassifier(
            n_estimators=200,  # Increased for better performance
            max_depth=15,      # Deeper trees for complex patterns
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',  # Use sqrt of features for each split
            class_weight='balanced',  # Handle class imbalance
            random_state=42,
            n_jobs=-1  # Use all available cores
        )
        
        # Train the model
        self.model.fit(self.X_train, self.y_train)
        logger.info("Model training completed")

    def _train_with_grid_search(self):
        """Train model with hyperparameter tuning"""
        # Define parameter grid
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None]
        }
        
        # Create base model
        rf = RandomForestClassifier(
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        # Perform grid search
        grid_search = GridSearchCV(
            rf, param_grid, 
            cv=5, 
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(self.X_train, self.y_train)
        
        # Use best model
        self.model = grid_search.best_estimator_
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best cross-validation score: {grid_search.best_score_:.3f}")

    def evaluate_model(self):
        """Evaluate the trained model"""
        logger.info("Evaluating model performance...")
        
        try:
            # Make predictions
            y_pred_train = self.model.predict(self.X_train)
            y_pred_test = self.model.predict(self.X_test)
            
            # Calculate accuracies
            train_accuracy = accuracy_score(self.y_train, y_pred_train)
            test_accuracy = accuracy_score(self.y_test, y_pred_test)
            
            logger.info(f"Training accuracy: {train_accuracy:.3f}")
            logger.info(f"Test accuracy: {test_accuracy:.3f}")
            
            # Cross-validation score
            cv_scores = cross_val_score(self.model, self.X_train, self.y_train, cv=5)
            logger.info(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            
            # Detailed classification report
            target_names = self.label_encoder.classes_
            logger.info("\nClassification Report:")
            logger.info(classification_report(self.y_test, y_pred_test, target_names=target_names))
            
            # Feature importance analysis
            self._analyze_feature_importance()
            
            # Check for overfitting
            if train_accuracy - test_accuracy > 0.1:
                logger.warning("Potential overfitting detected (train accuracy >> test accuracy)")
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            raise

    def _analyze_feature_importance(self, top_n=20):
        """Analyze and log feature importance"""
        logger.info(f"Analyzing top {top_n} feature importances...")
        
        try:
            # Get feature importances
            importances = self.model.feature_importances_
            
            # Create feature importance dataframe
            feature_importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            # Log top features
            logger.info(f"\nTop {top_n} Most Important Features:")
            for i, (_, row) in enumerate(feature_importance_df.head(top_n).iterrows()):
                logger.info(f"{i+1:2d}. {row['feature']:20s} : {row['importance']:.4f}")
            
            # Save feature importance for later analysis
            feature_importance_path = os.path.join(self.output_dir, 'feature_importance.csv')
            feature_importance_df.to_csv(feature_importance_path, index=False)
            logger.info(f"Feature importance saved to {feature_importance_path}")
            
        except Exception as e:
            logger.error(f"Error analyzing feature importance: {str(e)}")

    def save_model(self):
        """Save the trained model and components"""
        logger.info("Saving model components...")
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Save model
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {self.model_path}")
            
            # Save vectorizer
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            logger.info(f"Vectorizer saved to {self.vectorizer_path}")
            
            # Save label encoder
            with open(self.encoder_path, 'wb') as f:
                pickle.dump(self.label_encoder, f)
            logger.info(f"Label encoder saved to {self.encoder_path}")
            
            # Save metadata
            metadata = {
                'training_date': datetime.now().isoformat(),
                'model_type': 'RandomForestClassifier',
                'feature_count': len(self.feature_names),
                'classes': list(self.label_encoder.classes_),
                'training_samples': self.X_train.shape[0],
                'test_samples': self.X_test.shape[0],
                'test_accuracy': accuracy_score(self.y_test, self.model.predict(self.X_test)),
                'model_parameters': self.model.get_params()
            }
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            logger.info(f"Metadata saved to {self.metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def run_training_pipeline(self, hyperparameter_tuning=False):
        """Run the complete training pipeline"""
        logger.info("Starting EcoTide ML training pipeline...")
        start_time = datetime.now()
        
        try:
            # Step 1: Load and prepare data
            X, y = self.load_and_prepare_data()
            
            # Step 2: Create features
            X_features = self.create_features(X)
            
            # Step 3: Encode labels
            y_encoded = self.encode_labels(y)
            
            # Step 4: Split data
            self.split_data(X_features, y_encoded)
            
            # Step 5: Train model
            self.train_model(hyperparameter_tuning=hyperparameter_tuning)
            
            # Step 6: Save model
            self.save_model()
            
            # Training complete
            end_time = datetime.now()
            training_time = end_time - start_time
            logger.info(f"Training pipeline completed successfully in {training_time}")
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {str(e)}")
            raise

def main():
    """Main training script entry point"""
    parser = argparse.ArgumentParser(description='Train EcoTide sustainability scoring model')
    parser.add_argument('--data', type=str, default='raw_products.csv',
                        help='Path to training data CSV file')
    parser.add_argument('--output', type=str, default='../ecotide-backend',
                        help='Output directory for saved models')
    parser.add_argument('--tune', action='store_true',
                        help='Perform hyperparameter tuning')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize trainer
        trainer = SustainabilityModelTrainer(
            data_path=args.data,
            output_dir=args.output
        )
        
        # Run training pipeline
        trainer.run_training_pipeline(hyperparameter_tuning=args.tune)
        
        logger.info("Training completed successfully!")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
