import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/globals.css'

// This is the main entry point for development
// The actual extension uses separate entry points for popup, content, and background scripts
function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-eco-primary mb-8">EcoTide Development</h1>
        <p className="text-gray-600">
          This is the development environment for EcoTide Chrome Extension.
          The actual extension components are in the popup, content, and background directories.
        </p>
      </div>
    </div>
  )
}

if (document.getElementById('root')) {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
}
