// Storage utilities for Chrome extension local storage

/**
 * Save eco data to Chrome storage
 * @param {Object} data - Eco data to save
 * @returns {Promise<void>}
 */
export async function saveEcoData(data) {
  try {
    const response = await chrome.runtime.sendMessage({ 
      action: 'saveEcoData', 
      data: data 
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    console.log('EcoTide Storage: Data saved successfully');
  } catch (error) {
    console.error('EcoTide Storage: Error saving data:', error);
    throw error;
  }
}

/**
 * Get all eco data from Chrome storage
 * @returns {Promise<Array>} Array of eco data entries
 */
export async function getEcoData() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getEcoData' });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response || [];
  } catch (error) {
    console.error('EcoTide Storage: Error getting data:', error);
    return [];
  }
}

/**
 * Clear all eco data from Chrome storage
 * @returns {Promise<void>}
 */
export async function clearEcoData() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'clearEcoData' });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    console.log('EcoTide Storage: Data cleared successfully');
  } catch (error) {
    console.error('EcoTide Storage: Error clearing data:', error);
    throw error;
  }
}

/**
 * Get extension settings
 * @returns {Promise<Object>} Settings object
 */
export async function getSettings() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getSettings' });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    return response || {
      notificationsEnabled: true,
      autoScan: true,
      apiEndpoint: 'http://localhost:8000'
    };
  } catch (error) {
    console.error('EcoTide Storage: Error getting settings:', error);
    return {
      notificationsEnabled: true,
      autoScan: true,
      apiEndpoint: 'http://localhost:8000'
    };
  }
}

/**
 * Update extension settings
 * @param {Object} settings - Settings to update
 * @returns {Promise<void>}
 */
export async function updateSettings(settings) {
  try {
    const response = await chrome.runtime.sendMessage({ 
      action: 'updateSettings', 
      settings: settings 
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    console.log('EcoTide Storage: Settings updated successfully');
  } catch (error) {
    console.error('EcoTide Storage: Error updating settings:', error);
    throw error;
  }
}

/**
 * Save user progress data (badges, milestones, etc.)
 * @param {Object} progress - Progress data
 * @returns {Promise<void>}
 */
export async function saveProgress(progress) {
  try {
    const result = await chrome.storage.local.get(['userProgress']);
    const currentProgress = result.userProgress || {};
    
    const updatedProgress = {
      ...currentProgress,
      ...progress,
      lastUpdated: Date.now()
    };
    
    await chrome.storage.local.set({ userProgress: updatedProgress });
    console.log('EcoTide Storage: Progress saved successfully');
  } catch (error) {
    console.error('EcoTide Storage: Error saving progress:', error);
    throw error;
  }
}

/**
 * Get user progress data
 * @returns {Promise<Object>} Progress data
 */
export async function getProgress() {
  try {
    const result = await chrome.storage.local.get(['userProgress']);
    return result.userProgress || {
      badges: [],
      totalCo2Saved: 0,
      sustainableChoices: 0,
      weeklyGoals: {},
      achievements: []
    };
  } catch (error) {
    console.error('EcoTide Storage: Error getting progress:', error);
    return {
      badges: [],
      totalCo2Saved: 0,
      sustainableChoices: 0,
      weeklyGoals: {},
      achievements: []
    };
  }
}

/**
 * Cache sustainability data for products
 * @param {string} productKey - Unique product identifier
 * @param {Object} sustainabilityData - Sustainability data to cache
 * @returns {Promise<void>}
 */
export async function cacheSustainabilityData(productKey, sustainabilityData) {
  try {
    const result = await chrome.storage.local.get(['sustainabilityCache']);
    const cache = result.sustainabilityCache || {};
    
    // Add timestamp for cache expiration
    cache[productKey] = {
      ...sustainabilityData,
      cachedAt: Date.now()
    };
    
    // Keep cache size manageable (max 500 entries)
    const cacheKeys = Object.keys(cache);
    if (cacheKeys.length > 500) {
      // Remove oldest entries
      const sortedKeys = cacheKeys.sort((a, b) => cache[a].cachedAt - cache[b].cachedAt);
      for (let i = 0; i < 100; i++) {
        delete cache[sortedKeys[i]];
      }
    }
    
    await chrome.storage.local.set({ sustainabilityCache: cache });
    console.log('EcoTide Storage: Sustainability data cached for:', productKey);
  } catch (error) {
    console.error('EcoTide Storage: Error caching sustainability data:', error);
  }
}

/**
 * Get cached sustainability data for a product
 * @param {string} productKey - Unique product identifier
 * @returns {Promise<Object|null>} Cached sustainability data or null
 */
export async function getCachedSustainabilityData(productKey) {
  try {
    const result = await chrome.storage.local.get(['sustainabilityCache']);
    const cache = result.sustainabilityCache || {};
    const cachedData = cache[productKey];
    
    if (!cachedData) {
      return null;
    }
    
    // Check if cache is still valid (24 hours)
    const cacheAge = Date.now() - cachedData.cachedAt;
    const maxCacheAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
    
    if (cacheAge > maxCacheAge) {
      console.log('EcoTide Storage: Cache expired for:', productKey);
      return null;
    }
    
    console.log('EcoTide Storage: Retrieved cached data for:', productKey);
    return cachedData;
  } catch (error) {
    console.error('EcoTide Storage: Error getting cached data:', error);
    return null;
  }
}

/**
 * Clear cached sustainability data
 * @returns {Promise<void>}
 */
export async function clearSustainabilityCache() {
  try {
    await chrome.storage.local.remove(['sustainabilityCache']);
    console.log('EcoTide Storage: Sustainability cache cleared');
  } catch (error) {
    console.error('EcoTide Storage: Error clearing cache:', error);
  }
}

/**
 * Get storage usage statistics
 * @returns {Promise<Object>} Storage usage stats
 */
export async function getStorageStats() {
  try {
    const result = await chrome.storage.local.get(null);
    const stats = {
      ecoDataCount: result.ecoData ? result.ecoData.length : 0,
      cacheSize: result.sustainabilityCache ? Object.keys(result.sustainabilityCache).length : 0,
      hasProgress: !!result.userProgress,
      hasSettings: !!result.settings,
      totalKeys: Object.keys(result).length
    };
    
    return stats;
  } catch (error) {
    console.error('EcoTide Storage: Error getting storage stats:', error);
    return {
      ecoDataCount: 0,
      cacheSize: 0,
      hasProgress: false,
      hasSettings: false,
      totalKeys: 0
    };
  }
}

// Export storage configuration
export const STORAGE_CONFIG = {
  MAX_ECO_DATA_ENTRIES: 100,
  MAX_CACHE_ENTRIES: 500,
  CACHE_EXPIRATION_HOURS: 24,
  DEFAULT_SETTINGS: {
    notificationsEnabled: true,
    autoScan: true,
    apiEndpoint: 'http://localhost:8000'
  }
};
