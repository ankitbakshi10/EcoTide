import React, { useState, useEffect } from 'react';
import { getSustainabilityScore } from '../utils/api.js';
import { saveEcoData, getEcoData } from '../utils/storage.js';

const SustainabilityOverlay = ({ productTitle, productASIN, position }) => {
  const [sustainabilityData, setSustainabilityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetchSustainabilityData();
  }, [productTitle, productASIN]);

  const fetchSustainabilityData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getSustainabilityScore(productTitle || '', productASIN || '');
      setSustainabilityData(data);
      
      // Save to local storage for dashboard
      await saveEcoData({
        product: productTitle,
        grade: data.grade,
        co2_impact: data.co2_impact,
        timestamp: Date.now()
      });
      
    } catch (err) {
      console.error('Error fetching sustainability data:', err);
      setError('Failed to load sustainability data');
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    const colors = {
      'A': 'bg-grade-A text-white',
      'B': 'bg-grade-B text-white',
      'C': 'bg-grade-C text-black',
      'D': 'bg-grade-D text-white',
      'E': 'bg-grade-E text-white'
    };
    return colors[grade] || 'bg-gray-500 text-white';
  };

  const getGradeDescription = (grade) => {
    const descriptions = {
      'A': 'Excellent sustainability',
      'B': 'Good sustainability',
      'C': 'Average sustainability',
      'D': 'Below average sustainability',
      'E': 'Poor sustainability'
    };
    return descriptions[grade] || 'Unknown sustainability';
  };

  if (loading) {
    return (
      <div className="ecotide-overlay" style={{ 
        position: 'absolute', 
        top: position.top, 
        left: position.left,
        zIndex: 10000 
      }}>
        <div className="bg-white border border-eco-primary rounded-lg shadow-lg p-3 max-w-xs">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-eco-primary"></div>
            <span className="text-sm text-gray-600">Loading eco data...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ecotide-overlay" style={{ 
        position: 'absolute', 
        top: position.top, 
        left: position.left,
        zIndex: 10000 
      }}>
        <div className="bg-red-50 border border-red-200 rounded-lg shadow-lg p-3 max-w-xs">
          <div className="flex items-center space-x-2">
            <span className="text-red-600 text-sm">⚠️</span>
            <span className="text-sm text-red-600">Unable to load sustainability data</span>
          </div>
        </div>
      </div>
    );
  }

  if (!sustainabilityData) return null;

  return (
    <div className="ecotide-overlay" style={{ 
      position: 'absolute', 
      top: position.top, 
      left: position.left,
      zIndex: 10000 
    }}>
      <div className="bg-white border-2 border-eco-primary rounded-lg shadow-xl max-w-sm">
        {/* Header */}
        <div className="bg-eco-primary text-white px-4 py-2 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-lg">🌱</span>
              <span className="font-semibold text-sm">EcoTide</span>
            </div>
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-white hover:text-eco-light transition-colors"
            >
              {isExpanded ? '−' : '+'}
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Grade Display */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${getGradeColor(sustainabilityData.grade)}`}>
                {sustainabilityData.grade}
              </div>
              <div>
                <div className="font-semibold text-gray-800">{getGradeDescription(sustainabilityData.grade)}</div>
                <div className="text-sm text-gray-600">Sustainability Grade</div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-blue-50 rounded-lg p-2">
              <div className="text-xs text-blue-600 font-medium">CO₂ Impact</div>
              <div className="text-sm font-bold text-blue-800">{sustainabilityData.co2_impact}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-2">
              <div className="text-xs text-green-600 font-medium">Recyclable</div>
              <div className="text-sm font-bold text-green-800">
                {sustainabilityData.recyclable ? 'Yes' : 'No'}
              </div>
            </div>
          </div>

          {/* Expanded Details */}
          {isExpanded && (
            <div className="border-t pt-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Renewable Materials:</span>
                <span className="font-medium">{sustainabilityData.renewable_materials ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Packaging Impact:</span>
                <span className="font-medium">{sustainabilityData.packaging_score || 'N/A'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Supply Chain:</span>
                <span className="font-medium">{sustainabilityData.supply_chain_score || 'N/A'}</span>
              </div>
              
              {sustainabilityData.green_message && (
                <div className="bg-eco-light rounded-lg p-2 mt-3">
                  <div className="text-xs text-eco-dark font-medium mb-1">💡 Green Tip</div>
                  <div className="text-sm text-eco-dark">{sustainabilityData.green_message}</div>
                </div>
              )}
            </div>
          )}

          {/* Action Button */}
          <button 
            onClick={() => chrome.runtime.sendMessage({action: 'openDashboard'})}
            className="w-full bg-eco-primary text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-eco-secondary transition-colors mt-3"
          >
            View Eco Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default SustainabilityOverlay;
