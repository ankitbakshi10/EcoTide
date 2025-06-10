import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import EcoDashboard from '../components/EcoDashboard.jsx';
import '../styles/globals.css';

const PopupApp = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [settings, setSettings] = useState({
    notificationsEnabled: true,
    autoScan: true,
    apiEndpoint: 'http://localhost:8000'
  });
  const [stats, setStats] = useState({
    totalProducts: 0,
    averageGrade: 'N/A',
    co2Saved: 0
  });

  useEffect(() => {
    loadSettings();
    loadStats();
    
    // Check if we should show dashboard based on URL hash
    if (window.location.hash === '#dashboard') {
      setCurrentView('dashboard');
    }
  }, []);

  const loadSettings = async () => {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'getSettings' });
      if (response && !response.error) {
        setSettings(response);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const loadStats = async () => {
    try {
      const ecoData = await chrome.runtime.sendMessage({ action: 'getEcoData' });
      if (ecoData && !ecoData.error) {
        calculateStats(ecoData);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const calculateStats = (data) => {
    if (!data || data.length === 0) {
      setStats({ totalProducts: 0, averageGrade: 'N/A', co2Saved: 0 });
      return;
    }

    const totalProducts = data.length;
    const gradeValues = { A: 5, B: 4, C: 3, D: 2, E: 1 };
    const averageGradeValue = data.reduce((sum, item) => sum + (gradeValues[item.grade] || 0), 0) / totalProducts;
    const averageGrade = Object.keys(gradeValues).find(key => gradeValues[key] === Math.round(averageGradeValue)) || 'C';
    
    const goodChoices = data.filter(item => ['A', 'B'].includes(item.grade)).length;
    const co2Saved = Math.round(goodChoices * 2.5 * 10) / 10;

    setStats({ totalProducts, averageGrade, co2Saved });
  };

  const updateSettings = async (newSettings) => {
    try {
      await chrome.runtime.sendMessage({ 
        action: 'updateSettings', 
        settings: newSettings 
      });
      setSettings(prev => ({ ...prev, ...newSettings }));
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const openFullDashboard = () => {
    chrome.tabs.create({
      url: chrome.runtime.getURL('src/popup/popup.html') + '#dashboard'
    });
    window.close();
  };

  const scanCurrentPage = async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      await chrome.tabs.sendMessage(tab.id, { action: 'scanProducts' });
    } catch (error) {
      console.error('Error scanning current page:', error);
    }
  };

  if (currentView === 'dashboard' && window.location.hash === '#dashboard') {
    return <EcoDashboard />;
  }

  return (
    <div className="w-80 h-96 bg-gray-50">
      {/* Header */}
      <div className="bg-eco-primary text-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🌱</span>
            <h1 className="text-lg font-semibold">EcoTide</h1>
          </div>
          <button 
            onClick={() => setCurrentView(currentView === 'popup' ? 'settings' : 'popup')}
            className="text-white hover:text-eco-light transition-colors"
          >
            {currentView === 'popup' ? '⚙️' : '🏠'}
          </button>
        </div>
      </div>

      {currentView === 'popup' && (
        <div className="p-4 space-y-4">
          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-white rounded-lg p-2 shadow-sm">
              <div className="text-lg font-bold text-eco-primary">{stats.totalProducts}</div>
              <div className="text-xs text-gray-600">Products</div>
            </div>
            <div className="bg-white rounded-lg p-2 shadow-sm">
              <div className="text-lg font-bold text-eco-secondary">{stats.averageGrade}</div>
              <div className="text-xs text-gray-600">Avg Grade</div>
            </div>
            <div className="bg-white rounded-lg p-2 shadow-sm">
              <div className="text-lg font-bold text-eco-primary">{stats.co2Saved}kg</div>
              <div className="text-xs text-gray-600">CO₂ Saved</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2">
            <button 
              onClick={scanCurrentPage}
              className="w-full bg-eco-primary text-white py-2 px-4 rounded-lg hover:bg-eco-secondary transition-colors text-sm font-medium"
            >
              Scan Current Page
            </button>
            
            <button 
              onClick={openFullDashboard}
              className="w-full bg-white border border-eco-primary text-eco-primary py-2 px-4 rounded-lg hover:bg-eco-light transition-colors text-sm font-medium"
            >
              Open Full Dashboard
            </button>
          </div>

          {/* Quick Info */}
          <div className="bg-white rounded-lg p-3 shadow-sm">
            <h3 className="font-medium text-gray-800 mb-2">How it works:</h3>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Browse supported e-commerce sites</li>
              <li>• See sustainability grades on products</li>
              <li>• Track your eco-friendly choices</li>
              <li>• Earn badges for sustainable shopping</li>
            </ul>
          </div>

          {/* Supported Sites */}
          <div className="bg-eco-light rounded-lg p-3">
            <h3 className="font-medium text-eco-dark mb-2">Supported Sites:</h3>
            <div className="flex space-x-2">
              <span className="bg-white px-2 py-1 rounded text-xs text-eco-dark">Amazon</span>
              <span className="bg-white px-2 py-1 rounded text-xs text-eco-dark">eBay</span>
            </div>
          </div>
        </div>
      )}

      {currentView === 'settings' && (
        <div className="p-4 space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">Settings</h2>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Enable Notifications</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notificationsEnabled}
                  onChange={(e) => updateSettings({ notificationsEnabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-eco-primary/25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-eco-primary"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Auto-scan Products</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autoScan}
                  onChange={(e) => updateSettings({ autoScan: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-eco-primary/25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-eco-primary"></div>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">API Endpoint</label>
            <input
              type="text"
              value={settings.apiEndpoint}
              onChange={(e) => updateSettings({ apiEndpoint: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-eco-primary"
              placeholder="http://localhost:8000"
            />
          </div>

          <div className="space-y-2">
            <button 
              onClick={() => chrome.runtime.sendMessage({ action: 'clearEcoData' })}
              className="w-full bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
            >
              Clear All Data
            </button>
          </div>

          <div className="text-xs text-gray-500 pt-2 border-t">
            <p>EcoTide v1.0.0</p>
            <p>Promoting sustainable shopping choices</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Initialize React app
if (document.getElementById('popup-root')) {
  const root = ReactDOM.createRoot(document.getElementById('popup-root'));
  root.render(<PopupApp />);
}

export default PopupApp;
