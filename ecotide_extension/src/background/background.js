// Background service worker for EcoTide Chrome Extension

chrome.runtime.onInstalled.addListener((details) => {
  console.log('EcoTide: Extension installed', details);
  
  // Set up initial storage
  chrome.storage.local.set({
    ecoData: [],
    settings: {
      notificationsEnabled: true,
      autoScan: true,
      apiEndpoint: 'http://localhost:8000'
    }
  });

  // Show welcome notification
  chrome.notifications.create('welcome', {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'EcoTide Installed!',
    message: 'Start shopping sustainably with real-time eco grades.'
  });
});

// Handle tab updates to scan for products
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const url = new URL(tab.url);
    const supportedSites = ['amazon.com', 'ebay.com'];
    
    if (supportedSites.some(site => url.hostname.includes(site))) {
      console.log('EcoTide: Detected supported e-commerce site:', url.hostname);
      
      // Inject content script if not already present
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['src/content/content.js']
      }).catch(err => {
        // Content script might already be injected
        console.log('EcoTide: Content script injection skipped:', err.message);
      });

      // Trigger product scan
      setTimeout(() => {
        chrome.tabs.sendMessage(tabId, { action: 'scanProducts' }).catch(err => {
          console.log('EcoTide: Could not send scan message:', err.message);
        });
      }, 2000);
    }
  }
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('EcoTide: Received message:', request);

  switch (request.action) {
    case 'openDashboard':
      openDashboard();
      break;

    case 'getSustainabilityData':
      handleSustainabilityRequest(request.productTitle, request.asin)
        .then(sendResponse)
        .catch(error => {
          console.error('EcoTide: Error getting sustainability data:', error);
          sendResponse({ error: error.message });
        });
      return true; // Keep message channel open for async response

    case 'saveEcoData':
      saveEcoData(request.data)
        .then(() => sendResponse({ success: true }))
        .catch(error => {
          console.error('EcoTide: Error saving eco data:', error);
          sendResponse({ error: error.message });
        });
      return true;

    case 'getEcoData':
      getEcoData()
        .then(sendResponse)
        .catch(error => {
          console.error('EcoTide: Error getting eco data:', error);
          sendResponse({ error: error.message });
        });
      return true;

    case 'clearEcoData':
      clearEcoData()
        .then(() => sendResponse({ success: true }))
        .catch(error => {
          console.error('EcoTide: Error clearing eco data:', error);
          sendResponse({ error: error.message });
        });
      return true;

    case 'updateSettings':
      updateSettings(request.settings)
        .then(() => sendResponse({ success: true }))
        .catch(error => {
          console.error('EcoTide: Error updating settings:', error);
          sendResponse({ error: error.message });
        });
      return true;
  }
});

// Open dashboard in new tab
function openDashboard() {
  chrome.tabs.create({
    url: chrome.runtime.getURL('src/popup/popup.html') + '#dashboard'
  });
}

// Handle sustainability data requests
async function handleSustainabilityRequest(productTitle, asin) {
  try {
    const settings = await getSettings();
    const apiEndpoint = settings.apiEndpoint || 'http://localhost:8000';
    
    const response = await fetch(`${apiEndpoint}/api/sustainability`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_title: productTitle || '',
        asin: asin || ''
      })
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('EcoTide: API request failed:', error);
    
    // Return fallback data
    return {
      grade: 'C',
      co2_impact: 'Unknown',
      recyclable: false,
      renewable_materials: false,
      packaging_score: 'N/A',
      supply_chain_score: 'N/A',
      green_message: 'Unable to connect to sustainability service. Please check your connection.'
    };
  }
}

// Storage helper functions
async function saveEcoData(newData) {
  const result = await chrome.storage.local.get(['ecoData']);
  const ecoData = result.ecoData || [];
  
  ecoData.push(newData);
  
  // Keep only last 100 entries
  if (ecoData.length > 100) {
    ecoData.splice(0, ecoData.length - 100);
  }
  
  await chrome.storage.local.set({ ecoData });
}

async function getEcoData() {
  const result = await chrome.storage.local.get(['ecoData']);
  return result.ecoData || [];
}

async function clearEcoData() {
  await chrome.storage.local.set({ ecoData: [] });
}

async function getSettings() {
  const result = await chrome.storage.local.get(['settings']);
  return result.settings || {
    notificationsEnabled: true,
    autoScan: true,
    apiEndpoint: 'http://localhost:8000'
  };
}

async function updateSettings(newSettings) {
  const currentSettings = await getSettings();
  const updatedSettings = { ...currentSettings, ...newSettings };
  await chrome.storage.local.set({ settings: updatedSettings });
}

// Periodic notifications for sustainable shopping tips
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'weeklyEcoTip') {
    showWeeklyEcoTip();
  }
});

// Set up weekly eco tip alarm
chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create('weeklyEcoTip', {
    delayInMinutes: 60 * 24 * 7, // 1 week
    periodInMinutes: 60 * 24 * 7
  });
});

async function showWeeklyEcoTip() {
  const settings = await getSettings();
  if (!settings.notificationsEnabled) return;

  const tips = [
    'Look for products with minimal packaging to reduce waste!',
    'Choose items made from recycled materials when possible.',
    'Consider the carbon footprint of shipping when shopping online.',
    'Buy only what you need to reduce overall consumption.',
    'Support brands committed to sustainability practices.'
  ];

  const randomTip = tips[Math.floor(Math.random() * tips.length)];

  chrome.notifications.create('weeklyTip', {
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: '🌱 Weekly Eco Tip',
    message: randomTip
  });
}

// Handle notification clicks
chrome.notifications.onClicked.addListener((notificationId) => {
  if (notificationId === 'welcome' || notificationId === 'weeklyTip') {
    openDashboard();
  }
  chrome.notifications.clear(notificationId);
});

console.log('EcoTide: Background script loaded');
