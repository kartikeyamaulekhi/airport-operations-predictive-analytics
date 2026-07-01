# Data 
 
Raw and processed data files are gitignored (too large for version control). 
 
To reproduce: 
1. Install kaggle CLI: pip install kaggle 
2. Set KAGGLE_API_TOKEN environment variable 
3. Run: kaggle datasets download -d sriharshaeedala/airline-delay -p data --unzip 
4. Run: python scripts/clean_and_engineer.py 
