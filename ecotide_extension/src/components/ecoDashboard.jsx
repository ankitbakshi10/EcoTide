import React, { useState, useEffect } from 'react';
import { getEcoData, clearEcoData } from '../utils/storage.js';

const EcoDashboard = () => {
  const [ecoData, setEcoData] = useState([]);
  const [stats, setStats] = useState({
    totalProducts: 0,
    averageGrade: 'N/A',
    co2Saved: 0,
    badges: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEcoData();
  }, []);

  const loadEcoData = async () => {
    try {
      const data = await getEcoData();
      setEcoData(data);
      calculateStats(data);
    } catch (error) {
      console.error('Error loading eco data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (data) => {
    if (!data || data.length === 0) {
      setStats({
        totalProducts: 0,
        averageGrade: 'N/A',
        co2Saved: 0,
        badges: []
      });
      return;
    }

    const totalProducts = data.length;
    const gradeValues = { A: 5, B: 4, C: 3, D: 2, E: 1 };
    const averageGradeValue = data.reduce((sum, item) => sum + (gradeValues[item.grade] || 0), 0) / totalProducts;
    const averageGrade = Object.keys(gradeValues).find(key => gradeValues[key] === Math.round(averageGradeValue)) || 'C';
    
    // Calculate estimated CO2 saved based on good choices (A and B grades)
    const goodChoices = data.filter(item => ['A', 'B'].includes(item.grade)).length;
    const co2Saved = goodChoices * 2.5; // Estimated 2.5kg CO2 saved per sustainable choice

    // Calculate badges
    const badges = [];
    if (totalProducts >= 5) badges.push({ name: 'Eco Explorer', icon: '🌱', description: 'Checked 5+ products' });
    if (totalProducts >= 20) badges.push({ name: 'Green Shopper', icon: '🛒', description: 'Checked 20+ products' });
    if (goodChoices >= 10) badges.push({ name: 'Sustainability Champion', icon: '🏆', description: '10+ sustainable choices' });
    if (co2Saved >= 25) badges.push({ name: 'Carbon Saver', icon: '🌍', description: 'Saved 25kg+ CO₂' });

    setStats({
      totalProducts,
      averageGrade,
      co2Saved: Math.round(co2Saved * 10) / 10,
      badges
    });
  };

  const getGradeColor = (grade) => {
    const colors = {
      'A': 'text-grade-A',
      'B': 'text-grade-B',
      'C': 'text-grade-C',
      'D': 'text-grade-D',
      'E': 'text-grade-E'
    };
    return colors[grade] || 'text-gray-500';
  };

  const clearAllData = async () => {
    if (confirm('Are you sure you want to clear all eco data?')) {
      await clearEcoData();
      setEcoData([]);
      setStats({
        totalProducts: 0,
        averageGrade: 'N/A',
        co2Saved: 0,
        badges: []
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-eco-primary"></div>
          <span className="text-gray-600">Loading your eco dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 flex items-center">
                <span className="mr-3">🌱</span>
                EcoTide Dashboard
              </h1>
              <p className="text-gray-600 mt-1">Track your sustainable shopping journey</p>
            </div>
            <button
              onClick={clearAllData}
              className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
            >
              Clear Data
            </button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="bg-blue-100 rounded-lg p-3 mr-4">
                <span className="text-2xl">📊</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-800">{stats.totalProducts}</div>
                <div className="text-gray-600 text-sm">Products Checked</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="bg-green-100 rounded-lg p-3 mr-4">
                <span className="text-2xl">📈</span>
              </div>
              <div>
                <div className={`text-2xl font-bold ${getGradeColor(stats.averageGrade)}`}>
                  {stats.averageGrade}
                </div>
                <div className="text-gray-600 text-sm">Average Grade</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="bg-eco-light rounded-lg p-3 mr-4">
                <span className="text-2xl">🌍</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-eco-primary">{stats.co2Saved}kg</div>
                <div className="text-gray-600 text-sm">CO₂ Saved</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="bg-yellow-100 rounded-lg p-3 mr-4">
                <span className="text-2xl">🏆</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-800">{stats.badges.length}</div>
                <div className="text-gray-600 text-sm">Badges Earned</div>
              </div>
            </div>
          </div>
        </div>

        {/* Badges Section */}
        {stats.badges.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">🏆 Your Badges</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stats.badges.map((badge, index) => (
                <div key={index} className="bg-gradient-to-r from-eco-light to-green-100 rounded-lg p-4 border border-eco-primary">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-3">{badge.icon}</span>
                    <div className="font-semibold text-eco-dark">{badge.name}</div>
                  </div>
                  <div className="text-sm text-eco-dark opacity-80">{badge.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">📝 Recent Activity</h2>
          
          {ecoData.length === 0 ? (
            <div className="text-center py-8">
              <span className="text-4xl mb-4 block">🛒</span>
              <h3 className="text-lg font-medium text-gray-800 mb-2">No eco data yet</h3>
              <p className="text-gray-600">Start shopping on supported e-commerce sites to see sustainability insights!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {ecoData.slice(-10).reverse().map((item, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium text-gray-800 truncate max-w-md">
                      {item.product || 'Unknown Product'}
                    </div>
                    <div className="text-sm text-gray-600">
                      {new Date(item.timestamp).toLocaleDateString()} at {new Date(item.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-600">{item.co2_impact}</div>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white ${
                      item.grade === 'A' ? 'bg-grade-A' :
                      item.grade === 'B' ? 'bg-grade-B' :
                      item.grade === 'C' ? 'bg-grade-C' :
                      item.grade === 'D' ? 'bg-grade-D' :
                      'bg-grade-E'
                    }`}>
                      {item.grade}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Comparison with Average Shopper */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">📈 Impact Comparison</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-eco-primary">{stats.co2Saved}kg</div>
              <div className="text-gray-600">Your CO₂ Savings</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-400">12.5kg</div>
              <div className="text-gray-600">Average Shopper</div>
            </div>
          </div>
          <div className="mt-4 text-center">
            {stats.co2Saved > 12.5 ? (
              <div className="text-eco-primary font-medium">
                🎉 You're doing better than the average shopper!
              </div>
            ) : (
              <div className="text-gray-600">
                Keep making sustainable choices to exceed the average!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EcoDashboard;
