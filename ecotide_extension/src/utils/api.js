// API utilities for communicating with the backend

const DEFAULT_API_ENDPOINT = 'http://localhost:8000';

/**
 * Get sustainability score for a product
 * @param {string} productTitle - The product title
 * @param {string} asin - Amazon ASIN (optional)
 * @returns {Promise<Object>} Sustainability data
 */
export async function getSustainabilityScore(productTitle, asin = '') {
  try {
    // Get API endpoint from settings
    const settings = await getSettings();
    const apiEndpoint = settings.apiEndpoint || DEFAULT_API_ENDPOINT;
    
    console.log('EcoTide API: Requesting sustainability data for:', productTitle);
    
    const response = await fetch(`${apiEndpoint}/api/sustainability`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        product_title: productTitle,
        asin: asin
      })
    });

    if (!response.ok) {
      throw new Error(`API request failed with status: ${response.status}`);
    }

    const data = await response.json();
    
    // Validate response structure
    if (!data.grade || !data.co2_impact) {
      throw new Error('Invalid response format from API');
    }

    console.log('EcoTide API: Received sustainability data:', data);
    return data;

  } catch (error) {
    console.error('EcoTide API: Error fetching sustainability data:', error);
    
    // Return fallback data with error indication
    return {
      grade: 'C',
      co2_impact: 'Unknown',
      recyclable: false,
      renewable_materials: false,
      packaging_score: 'N/A',
      supply_chain_score: 'N/A',
      green_message: 'Unable to fetch sustainability data. Please check your connection and ensure the EcoTide backend is running.',
      error: true
    };
  }
}

/**
 * Test API connection
 * @returns {Promise<boolean>} True if API is accessible
 */
export async function testApiConnection() {
  try {
    const settings = await getSettings();
    const apiEndpoint = settings.apiEndpoint || DEFAULT_API_ENDPOINT;
    
    const response = await fetch(`${apiEndpoint}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    return response.ok;
  } catch (error) {
    console.error('EcoTide API: Connection test failed:', error);
    return false;
  }
}

/**
 * Get API health status
 * @returns {Promise<Object>} Health status information
 */
export async function getApiHealth() {
  try {
    const settings = await getSettings();
    const apiEndpoint = settings.apiEndpoint || DEFAULT_API_ENDPOINT;
    
    const response = await fetch(`${apiEndpoint}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('EcoTide API: Health check failed:', error);
    return {
      status: 'error',
      message: error.message
    };
  }
}

/**
 * Submit feedback about a sustainability score
 * @param {string} productTitle - Product title
 * @param {string} grade - Given grade
 * @param {string} feedback - User feedback
 * @returns {Promise<boolean>} Success status
 */
export async function submitFeedback(productTitle, grade, feedback) {
  try {
    const settings = await getSettings();
    const apiEndpoint = settings.apiEndpoint || DEFAULT_API_ENDPOINT;
    
    const response = await fetch(`${apiEndpoint}/api/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        product_title: productTitle,
        grade: grade,
        feedback: feedback,
        timestamp: new Date().toISOString()
      })
    });

    return response.ok;
  } catch (error) {
    console.error('EcoTide API: Feedback submission failed:', error);
    return false;
  }
}

/**
 * Get product suggestions based on current product
 * @param {string} productTitle - Current product title
 * @param {string} category - Product category (optional)
 * @returns {Promise<Array>} Array of alternative product suggestions
 */
export async function getProductSuggestions(productTitle, category = '') {
  try {
    const settings = await getSettings();
    const apiEndpoint = settings.apiEndpoint || DEFAULT_API_ENDPOINT;
    
    const response = await fetch(`${apiEndpoint}/api/suggestions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        product_title: productTitle,
        category: category
      })
    });

    if (!response.ok) {
      throw new Error(`Suggestions request failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('EcoTide API: Suggestions request failed:', error);
    return [];
  }
}

// Helper function to get settings (uses Chrome storage)
async function getSettings() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getSettings' });
    return response || { apiEndpoint: DEFAULT_API_ENDPOINT };
  } catch (error) {
    console.error('Error getting settings:', error);
    return { apiEndpoint: DEFAULT_API_ENDPOINT };
  }
}

// Export default configuration
export const API_CONFIG = {
  DEFAULT_ENDPOINT: DEFAULT_API_ENDPOINT,
  TIMEOUT: 10000, // 10 seconds
  RETRY_ATTEMPTS: 2
};
