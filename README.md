
#To create, activate virtual environment and install the dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

#To git commit
git init
git add .
git commit -m "Initial commit: working NSEstock screener"
git remote add origin https://github.com/wittyskull-git/stock-screener.git
git branch -m main     
git push -u origin main