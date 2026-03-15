# Smart Sandbag Server

## Setup Instructions for Labmates
1. Clone this repository to your computer `git clone httpsgithub.comZuonVuSmart-Sandbag.git`
2. Open your terminal inside the downloaded project folder.
3. Create a virtual environment
   - Windows `python -m venv venv`
   - MacLinux `python3 -m venv venv`
4. Activate the virtual environment
   - Windows `.venvScriptsactivate`
   - MacLinux `source venvbinactivate`
5. Install the required packages
   `pip install -r requirements.txt`
6. Apply database migrations (since `db.sqlite3` is ignored)
   `python manage.py migrate`
7. Start the server
   `python manage.py runserver`