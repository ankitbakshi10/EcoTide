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

