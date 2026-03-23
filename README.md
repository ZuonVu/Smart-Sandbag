# Smart Sandbag Server

## Setup Instructions for Labmates
1. Clone this repository to your computer `git clone httpsgithub.comZuonVuSmart-Sandbag.git`
2. Open your PowerShell terminal inside the downloaded project folder.
3. Create a virtual environment
   - Windows `python -m venv venv`
   - MacLinux `python3 -m venv venv`
4. Activate the virtual environment
   - Windows `.venvScriptsactivate`
   - MacLinux `source venvbinactivate`
5. Install the required packages
   `pip install -r requirements.txt`
6. Apply database migrations 
   `python manage.py migrate`
7. Start the server
   `python manage.py runserver`


## Arduino Setup (XIAO_code.ino)

To upload the XIAO_code.ino code to your Xiao Seeed microcontroller, you need to install two libraries via the Arduino IDE Library Manager.

1. Open the Arduino IDE.
2. Go to **Sketch** > **Include Library** > **Manage Libraries...** (or press `Ctrl+Shift+I`).
3. In the search bar, search for and install:
   * **ArduinoBLE** (by Arduino)
   * **LSM6DS3** (by Seeed Studio)
4. Select your specific XIAO board and port, then click **Upload**.
