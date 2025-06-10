// Content script for injecting sustainability overlays on product pages
import { getSustainabilityScore } from '../utils/api.js';
import { saveEcoData } from '../utils/storage.js';

class EcoTideContentScript {
  constructor() {
    this.overlays = new Map();
    this.observer = null;
    this.init();
  }

  init() {
    console.log('EcoTide: Content script initialized');
    this.setupMutationObserver();
    this.scanForProducts();
  }

  setupMutationObserver() {
    this.observer = new MutationObserver((mutations) => {
      let shouldScan = false;
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          shouldScan = true;
        }
      });
      if (shouldScan) {
        setTimeout(() => this.scanForProducts(), 1000);
      }
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  scanForProducts() {
    try {
      const currentSite = this.detectSite();
      console.log('EcoTide: Scanning for products on', currentSite);

      if (currentSite === 'amazon') {
        this.scanAmazonProducts();
      } else if (currentSite === 'ebay') {
        this.scanEbayProducts();
      }
    } catch (error) {
      console.error('EcoTide: Error scanning for products:', error);
    }
  }

  detectSite() {
    const hostname = window.location.hostname.toLowerCase();
    if (hostname.includes('amazon')) return 'amazon';
    if (hostname.includes('ebay')) return 'ebay';
    return 'unknown';
  }

  scanAmazonProducts() {
    // Amazon product page
    if (window.location.pathname.includes('/dp/')) {
      this.handleAmazonProductPage();
    } 
    // Amazon search results
    else if (window.location.pathname.includes('/s')) {
      this.handleAmazonSearchResults();
    }
  }

  handleAmazonProductPage() {
    const titleElement = document.querySelector('#productTitle, .product-title');
    const asinMatch = window.location.pathname.match(/\/dp\/([A-Z0-9]{10})/);
    
    if (titleElement && !this.overlays.has('product-page')) {
      const productTitle = titleElement.textContent.trim();
      const asin = asinMatch ? asinMatch[1] : '';
      
      console.log('EcoTide: Found Amazon product:', productTitle);
      
      const targetElement = document.querySelector('#apex_desktop, #centerCol, .s-main-slot');
      if (targetElement) {
        this.injectOverlay('product-page', productTitle, asin, targetElement);
      }
    }
  }

  handleAmazonSearchResults() {
    const productCards = document.querySelectorAll('[data-component-type="s-search-result"]');
    
    productCards.forEach((card, index) => {
      const overlayId = `search-result-${index}`;
      if (this.overlays.has(overlayId)) return;

      const titleElement = card.querySelector('h2 a span, .s-title-instructions-style span');
      const asinElement = card.querySelector('[data-asin]');
      
      if (titleElement && asinElement) {
        const productTitle = titleElement.textContent.trim();
        const asin = asinElement.getAttribute('data-asin');
        
        if (productTitle && asin) {
          console.log('EcoTide: Found search result product:', productTitle);
          this.injectOverlay(overlayId, productTitle, asin, card, true);
        }
      }
    });
  }

  scanEbayProducts() {
    // eBay product page
    if (window.location.pathname.includes('/itm/')) {
      this.handleEbayProductPage();
    }
    // eBay search results
    else if (window.location.pathname.includes('/sch/')) {
      this.handleEbaySearchResults();
    }
  }

  handleEbayProductPage() {
    const titleElement = document.querySelector('.x-item-title-label, #ebay-item-name');
    
    if (titleElement && !this.overlays.has('ebay-product-page')) {
      const productTitle = titleElement.textContent.trim();
      console.log('EcoTide: Found eBay product:', productTitle);
      
      const targetElement = document.querySelector('.vim', '.item-view');
      if (targetElement) {
        this.injectOverlay('ebay-product-page', productTitle, '', targetElement);
      }
    }
  }

  handleEbaySearchResults() {
    const productCards = document.querySelectorAll('.s-item');
    
    productCards.forEach((card, index) => {
      const overlayId = `ebay-search-result-${index}`;
      if (this.overlays.has(overlayId)) return;

      const titleElement = card.querySelector('.s-item__title');
      
      if (titleElement) {
        const productTitle = titleElement.textContent.trim();
        if (productTitle && !productTitle.includes('Shop on eBay')) {
          console.log('EcoTide: Found eBay search result:', productTitle);
          this.injectOverlay(overlayId, productTitle, '', card, true);
        }
      }
    });
  }

  async injectOverlay(overlayId, productTitle, asin, targetElement, isCompact = false) {
    try {
      // Create overlay container
      const overlayContainer = document.createElement('div');
      overlayContainer.id = `ecotide-overlay-${overlayId}`;
      overlayContainer.className = 'ecotide-overlay-container';
      overlayContainer.style.cssText = `
        position: relative;
        z-index: 10000;
        margin: 10px 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      `;

      // Create loading state
      overlayContainer.innerHTML = `
        <div class="ecotide-loading" style="
          background: white;
          border: 2px solid #22c55e;
          border-radius: 8px;
          padding: ${isCompact ? '8px 12px' : '12px 16px'};
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          display: flex;
          align-items: center;
          gap: 8px;
        ">
          <div style="
            width: 16px;
            height: 16px;
            border: 2px solid #22c55e;
            border-top: 2px solid transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          "></div>
          <span style="color: #374151; font-size: ${isCompact ? '12px' : '14px'};">
            Loading sustainability data...
          </span>
        </div>
      `;

      // Add CSS animation
      if (!document.getElementById('ecotide-styles')) {
        const style = document.createElement('style');
        style.id = 'ecotide-styles';
        style.textContent = `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          .ecotide-overlay-container:hover {
            transform: translateY(-2px);
            transition: transform 0.2s ease;
          }
        `;
        document.head.appendChild(style);
      }

      // Insert overlay
      if (isCompact) {
        targetElement.appendChild(overlayContainer);
      } else {
        targetElement.insertBefore(overlayContainer, targetElement.firstChild);
      }

      this.overlays.set(overlayId, overlayContainer);

      // Fetch sustainability data
      const sustainabilityData = await getSustainabilityScore(productTitle, asin);
      
      // Update overlay with data
      this.updateOverlay(overlayContainer, sustainabilityData, isCompact);

      // Save to storage
      await saveEcoData({
        product: productTitle,
        grade: sustainabilityData.grade,
        co2_impact: sustainabilityData.co2_impact,
        timestamp: Date.now()
      });

    } catch (error) {
      console.error('EcoTide: Error injecting overlay:', error);
      this.showErrorOverlay(overlayContainer, isCompact);
    }
  }

  updateOverlay(container, data, isCompact) {
    const gradeColors = {
      'A': '#22c55e',
      'B': '#84cc16', 
      'C': '#eab308',
      'D': '#f97316',
      'E': '#ef4444'
    };

    const gradeColor = gradeColors[data.grade] || '#6b7280';

    container.innerHTML = `
      <div style="
        background: white;
        border: 2px solid #22c55e;
        border-radius: 8px;
        padding: ${isCompact ? '8px 12px' : '12px 16px'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
      " onclick="chrome.runtime.sendMessage({action: 'openDashboard'})">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: ${isCompact ? '16px' : '18px'};">🌱</span>
            <span style="color: #22c55e; font-weight: 600; font-size: ${isCompact ? '12px' : '14px'};">
              EcoTide
            </span>
          </div>
          
          <div style="
            background: ${gradeColor};
            color: white;
            width: ${isCompact ? '24px' : '32px'};
            height: ${isCompact ? '24px' : '32px'};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: ${isCompact ? '12px' : '16px'};
          ">
            ${data.grade}
          </div>
          
          <div style="flex: 1;">
            <div style="color: #374151; font-weight: 500; font-size: ${isCompact ? '11px' : '13px'};">
              ${this.getGradeDescription(data.grade)}
            </div>
            <div style="color: #6b7280; font-size: ${isCompact ? '10px' : '12px'};">
              ${data.co2_impact} • ${data.recyclable ? 'Recyclable' : 'Not recyclable'}
            </div>
          </div>

          ${!isCompact ? `
            <div style="
              background: #f3f4f6;
              padding: 4px 8px;
              border-radius: 4px;
              font-size: 11px;
              color: #6b7280;
            ">
              Click for details
            </div>
          ` : ''}
        </div>
        
        ${data.green_message && !isCompact ? `
          <div style="
            margin-top: 8px;
            padding: 8px;
            background: #dcfce7;
            border-radius: 6px;
            font-size: 12px;
            color: #15803d;
          ">
            💡 ${data.green_message}
          </div>
        ` : ''}
      </div>
    `;
  }

  showErrorOverlay(container, isCompact) {
    container.innerHTML = `
      <div style="
        background: #fef2f2;
        border: 2px solid #fca5a5;
        border-radius: 8px;
        padding: ${isCompact ? '8px 12px' : '12px 16px'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      ">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="color: #ef4444; font-size: ${isCompact ? '14px' : '16px'};">⚠️</span>
          <span style="color: #dc2626; font-size: ${isCompact ? '12px' : '14px'};">
            Unable to load sustainability data
          </span>
        </div>
      </div>
    `;
  }

  getGradeDescription(grade) {
    const descriptions = {
      'A': 'Excellent sustainability',
      'B': 'Good sustainability', 
      'C': 'Average sustainability',
      'D': 'Below average',
      'E': 'Poor sustainability'
    };
    return descriptions[grade] || 'Unknown sustainability';
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    this.overlays.forEach((overlay) => {
      if (overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
      }
    });
    this.overlays.clear();
  }
}

// Initialize content script
let ecoTideScript = null;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeScript);
} else {
  initializeScript();
}

function initializeScript() {
  if (!ecoTideScript) {
    ecoTideScript = new EcoTideContentScript();
  }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scanProducts') {
    if (ecoTideScript) {
      ecoTideScript.scanForProducts();
    }
  }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (ecoTideScript) {
    ecoTideScript.destroy();
  }
});
