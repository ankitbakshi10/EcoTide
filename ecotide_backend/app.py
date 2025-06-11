from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import time
import uuid
from datetime import datetime
from sustainability_score import SustainabilityScorer
from simple_database import init_database, get_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# Initialize database connection
db = init_database()
logger.info("Database initialized successfully")

# Initialize sustainability scorer
scorer = SustainabilityScorer()

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'service': 'EcoTide Backend API',
        'version': '1.0.0',
        'status': 'operational',
        'endpoints': {
            'health': '/health',
            'sustainability': '/api/sustainability',
            'feedback': '/api/feedback',
            'suggestions': '/api/suggestions',
            'stats': '/api/stats',
            'categories': '/api/categories'
        },
        'database': db.get_health_status()['status'],
        'model_loaded': scorer.model is not None
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Update API usage stats
    try:
        db.update_stats({'inc_health_checks': 1})
    except Exception as e:
        logger.warning(f"Failed to update health check stats: {str(e)}")
    
    # Check database health
    db_health = db.get_health_status()
    
    return jsonify({
        'status': 'healthy' if db_health['status'] == 'healthy' else 'degraded',
        'service': 'EcoTide Backend',
        'version': '1.0.0',
        'model_loaded': scorer.model is not None,
        'database': db_health,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/sustainability', methods=['POST'])
def get_sustainability_score():
    """
    Get sustainability score for a product
    
    Request body:
    {
        "product_title": "Product name",
        "asin": "Amazon ASIN (optional)"
    }
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        product_title = data.get('product_title', '').strip()
        asin = data.get('asin', '').strip()
        
        if not product_title:
            return jsonify({'error': 'Product title is required'}), 400
        
        logger.info(f"Scoring product: {product_title[:50]}...")
        
        # Check if product already exists in database
        try:
            existing_product = None
            if asin:
                existing_product = db.find_product_by_asin(asin)
            if not existing_product:
                existing_product = db.find_product_by_title(product_title)
            
            if existing_product:
                # Update access count and return cached result
                db.increment_product_access(existing_product['product_id'])
                result = {
                    'grade': existing_product['sustainability_grade'],
                    'co2_impact': existing_product['co2_impact'],
                    'recyclable': existing_product['recyclable'],
                    'renewable_materials': existing_product['renewable_materials'],
                    'packaging_score': existing_product.get('packaging_score'),
                    'supply_chain_score': existing_product.get('supply_chain_score'),
                    'confidence': existing_product.get('confidence_score', 0.0),
                    'timestamp': existing_product['updated_at'],
                    'cached': True
                }
                logger.info(f"Returned cached score for product with grade: {result['grade']}")
            else:
                # Get new sustainability score
                result = scorer.score_product(product_title, asin)
                
                # Save product to database
                try:
                    product_data = {
                        'title': product_title,
                        'asin': asin if asin else None,
                        'sustainability_grade': result['grade'],
                        'co2_impact': result['co2_impact'],
                        'recyclable': result['recyclable'],
                        'renewable_materials': result['renewable_materials'],
                        'packaging_score': result.get('packaging_score'),
                        'supply_chain_score': result.get('supply_chain_score'),
                        'confidence_score': result.get('confidence', 0.0),
                        'source_website': request.headers.get('Referer', 'unknown'),
                        'times_accessed': 1
                    }
                    product_id = db.save_product(product_data)
                    logger.info(f"Saved new product to database with ID: {product_id}")
                    
                    # Save sustainability score record
                    score_data = {
                        'product_id': product_id,
                        'product_title': product_title,
                        'grade': result['grade'],
                        'confidence': result.get('confidence', 0.0),
                        'co2_impact': result['co2_impact'],
                        'recyclable': result['recyclable'],
                        'renewable_materials': result['renewable_materials'],
                        'packaging_score': result.get('packaging_score'),
                        'supply_chain_score': result.get('supply_chain_score'),
                        'green_message': result.get('green_message'),
                        'scoring_method': 'ml_model' if scorer.model else 'rule_based',
                        'processing_time_ms': int((time.time() - start_time) * 1000),
                        'request_ip': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', ''),
                        'source_website': request.headers.get('Referer', 'unknown')
                    }
                    db.save_sustainability_score(score_data)
                    
                except Exception as db_error:
                    logger.error(f"Error saving to database: {str(db_error)}")
                    # Continue without database save
                
                result['cached'] = False
                logger.info(f"Scored product with grade: {result['grade']}")
        
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Fall back to direct scoring without database
            result = scorer.score_product(product_title, asin)
            result['cached'] = False
        
        # Update API usage statistics
        try:
            processing_time = int((time.time() - start_time) * 1000)
            grade_field = f"grade_{result['grade'].lower()}_count"
            
            stats_updates = {
                'inc_sustainability_requests': 1,
                f'inc_{grade_field}': 1,
                'inc_total_processing_time_ms': processing_time
            }
            
            # Calculate new average response time
            current_stats = db.get_or_create_today_stats()
            current_avg = current_stats.get('avg_response_time_ms', 0)
            current_requests = current_stats.get('sustainability_requests', 0)
            new_avg = ((current_avg * current_requests) + processing_time) / (current_requests + 1)
            stats_updates['set_avg_response_time_ms'] = new_avg
            
            db.update_stats(stats_updates)
            
        except Exception as stats_error:
            logger.warning(f"Failed to update API stats: {str(stats_error)}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error scoring product: {str(e)}")
        
        # Update error count in stats
        try:
            db.update_stats({'inc_error_count': 1})
        except Exception:
            pass
        
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback about a sustainability score
    
    Request body:
    {
        "product_title": "Product name",
        "user_grade": "A-E",
        "system_grade": "A-E", 
        "feedback": "User feedback",
        "helpful": true/false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        product_title = data.get('product_title', '').strip()
        user_grade = data.get('grade', '').strip().upper()  # Support both 'grade' and 'user_grade'
        if not user_grade:
            user_grade = data.get('user_grade', '').strip().upper()
        system_grade = data.get('system_grade', '').strip().upper()
        feedback_text = data.get('feedback', '').strip()
        helpful = data.get('helpful')
        
        if not product_title:
            return jsonify({'error': 'Product title is required'}), 400
        
        if user_grade and user_grade not in ['A', 'B', 'C', 'D', 'E']:
            return jsonify({'error': 'User grade must be A, B, C, D, or E'}), 400
            
        if system_grade and system_grade not in ['A', 'B', 'C', 'D', 'E']:
            return jsonify({'error': 'System grade must be A, B, C, D, or E'}), 400
        
        logger.info(f"Received feedback for product: {product_title[:50]}")
        
        try:
            # Find the product in database
            product = db.find_product_by_title(product_title)
            product_id = product['product_id'] if product else str(uuid.uuid4())
            
            # Create feedback record
            feedback_data = {
                'product_id': product_id,
                'product_title': product_title,
                'user_grade': user_grade if user_grade else None,
                'system_grade': system_grade if system_grade else None,
                'feedback_text': feedback_text if feedback_text else None,
                'helpful': helpful,
                'user_session_id': request.headers.get('X-Session-ID', ''),
                'user_ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'processed': False
            }
            feedback_id = db.save_feedback(feedback_data)
            
            logger.info(f"Saved feedback with ID: {feedback_id}")
            
            # Update API stats
            db.update_stats({'inc_feedback_submissions': 1})
            
            return jsonify({
                'status': 'success',
                'message': 'Feedback received successfully',
                'feedback_id': feedback_id
            })
            
        except Exception as db_error:
            logger.error(f"Error saving feedback to database: {str(db_error)}")
            return jsonify({
                'status': 'success',
                'message': 'Feedback received successfully',
                'note': 'Database temporarily unavailable'
            })
    
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/suggestions', methods=['POST'])
def get_product_suggestions():
    """
    Get sustainable product suggestions based on current product
    
    Request body:
    {
        "product_title": "Current product name",
        "category": "Product category (optional)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        product_title = data.get('product_title', '').strip()
        category = data.get('category', '').strip()
        
        if not product_title:
            return jsonify({'error': 'Product title is required'}), 400
        
        logger.info(f"Getting suggestions for: {product_title[:50]}...")
        
        # Get suggestions from scorer
        suggestions = scorer.get_suggestions(product_title, category)
        
        # Save suggestion request to database
        try:
            suggestion_data = {
                'original_product_title': product_title,
                'original_product_category': category,
                'suggestions': suggestions,
                'suggestion_count': len(suggestions),
                'user_session_id': request.headers.get('X-Session-ID', ''),
                'request_ip': request.remote_addr
            }
            db.save_feedback(suggestion_data)  # Using feedback collection for suggestions
            
            # Update API stats
            db.update_stats({'inc_suggestion_requests': 1})
            
        except Exception as db_error:
            logger.error(f"Error saving suggestion request: {str(db_error)}")
        
        return jsonify({
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_api_stats():
    """Get API usage statistics"""
    try:
        # Get database statistics summary
        db_stats = db.get_stats_summary()
        
        # Get today's detailed stats
        today_stats = db.get_or_create_today_stats()
        
        # Combine with scorer stats if available
        scorer_stats = scorer.get_stats() if hasattr(scorer, 'get_stats') else {}
        
        combined_stats = {
            'database': db_stats,
            'today': today_stats,
            'service': {
                'uptime_hours': 24,  # Placeholder for service uptime
                'version': '1.0.0',
                'model_loaded': scorer.model is not None
            }
        }
        
        # Merge scorer stats if available
        if scorer_stats:
            combined_stats['scorer'] = scorer_stats
        
        return jsonify(combined_stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of supported product categories"""
    try:
        categories = scorer.get_supported_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/admin/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old database records"""
    try:
        data = request.get_json()
        days_to_keep = data.get('days_to_keep', 30) if data else 30
        
        # Perform cleanup
        cleanup_result = db.cleanup_old_data(days_to_keep)
        
        logger.info(f"Database cleanup completed: {cleanup_result}")
        
        return jsonify({
            'status': 'success',
            'message': 'Database cleanup completed',
            'result': cleanup_result
        })
    except Exception as e:
        logger.error(f"Error during database cleanup: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/admin/export', methods=['GET'])
def export_data():
    """Export database data for backup"""
    try:
        export_data = {
            'products': list(db.products.values()),
            'feedback': list(db.feedback.values()),
            'scores': list(db.scores.values()),
            'stats': list(db.stats.values()),
            'export_timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
        
        return jsonify(export_data)
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Load or train model on startup
    try:
        logger.info("Starting EcoTide Backend...")
        scorer.load_or_train_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        logger.info("Server will start but scoring may not work properly")
    
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
