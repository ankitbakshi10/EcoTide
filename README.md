<<<<<<< HEAD
# EcoTide
## Amazon HackOn
### Folder structure
```bash
ecotide/
│
├── ecotide-extension/              # React + Chrome extension frontend
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProductOverlay.js
│   │   │   ├── EcoDashboard.js
│   │   │   └── BadgeDisplay.js
│   │   ├── content.js              # Injected into Amazon product pages
│   │   ├── App.js
│   │   └── index.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js
│   ├── package.json
│   ├── .gitignore
│   └── README.md

├── ecotide-backend/               # Flask backend for grading, dashboard, DB
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── models/
│   │   │   └── sustain_model.pkl
│   │   ├── db/
│   │   │   └── database.py
│   │   └── utils/
│   │       └── sustainability_score.py
│   ├── run.py
│   ├── requirements.txt
│   ├── .env
│   ├── .gitignore
│   └── README.md

├── ecotide-ml/                    # Machine learning code and training
│   ├── data/
│   │   └── raw_products.csv
│   ├── notebooks/
│   │   └── model_training.ipynb
│   ├── models/
│   │   └── sustain_model.pkl
│   ├── scripts/
│   │   ├── train_model.py
│   │   └── evaluate_model.py
│   ├── requirements.txt
│   └── README.md

├── ecotide-firebase/             # Firebase Functions for group-buy, nudges
│   ├── functions/
│   │   ├── index.js
│   │   └── package.json
│   ├── firebase.json
│   └── .firebaserc

├── .vscode/                      # Optional: VS Code workspace settings
│   ├── settings.json
│   └── launch.json

└── README.md                     # Main project overview + instructions
=======
# EcoTide - Sustainable Shopping Assistant 🌱

EcoTide is a comprehensive Chrome extension that promotes sustainable shopping by providing real-time sustainability grades (A-E) for e-commerce products. Built with React, Flask, and machine learning, it helps users make environmentally conscious purchasing decisions.

![EcoTide Logo](https://img.shields.io/badge/EcoTide-Sustainable%20Shopping-22c55e?style=for-the-badge&logo=leaf)

## 🌟 Features

### 🎯 Core Functionality
- **Real-time Sustainability Scoring**: Get instant A-E grades for products on Amazon, eBay, and other e-commerce sites
- **Smart Overlay Injection**: Non-intrusive overlays that appear directly on product pages
- **Comprehensive Metrics**: CO₂ impact, recyclability, renewable materials, and packaging assessments
- **Personal Dashboard**: Track your eco-friendly choices, badges, and environmental impact
- **ML-Powered Analysis**: Advanced machine learning model trained on sustainability indicators

### 🚀 Technology Stack
- **Frontend**: React 18 + Tailwind CSS + Vite
- **Backend**: Flask + scikit-learn + pandas
- **ML Pipeline**: RandomForest classifier with TF-IDF features
- **Extension**: Chrome Extension Manifest v3
- **Development**: VS Code configuration included

### 📊 Sustainability Metrics
- **Grade A**: Excellent sustainability (organic, renewable, zero waste)
- **Grade B**: Good sustainability (recyclable, durable, energy efficient)
- **Grade C**: Average sustainability (standard products)
- **Grade D**: Below average (disposable, synthetic materials)
- **Grade E**: Poor sustainability (toxic, wasteful, harmful)

## 🏗️ Project Structure
>>>>>>> 3ff1239 (Update README and add setup script)

