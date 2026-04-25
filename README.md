# Smart Sandbag System 🥊

The Smart Sandbag System is an IoT-enabled sports technology platform designed to track, analyze, and store combat sports performance metrics. 

🚀 **Live App:** The system is now hosted in the cloud! End-users do not need to run this code locally. Simply **visit our live website and download the app** to connect to the bag, track workouts, earn achievement badges, and download CSV training data. Android users can install the site as a Progressive Web App (PWA) directly to their home screens.

---

## 🛠️ Developer Setup Instructions (For Labmates)
If you are developing new features, testing the database, or modifying the backend, follow these steps to run the local development server:

1. **Clone this repository** to your computer:
   `git clone https://github.com/ZuonVu/Smart-Sandbag.git`
2. **Open your terminal** (e.g., PowerShell) inside the downloaded project folder.
3. **Create a virtual environment:**
   * Windows: `python -m venv venv`
   * Mac/Linux: `python3 -m venv venv`
4. **Activate the virtual environment:**
   * Windows: `.\venv\Scripts\activate`
   * Mac/Linux: `source venv/bin/activate`
5. **Install the required packages:**
   `pip install -r requirements.txt`
6. **Apply database migrations:** `python manage.py migrate`
7. **Start the local server:**
   `python manage.py runserver`

---

## ⚡ Arduino Setup (XIAO_code.ino)

To upload the `XIAO_code.ino` firmware to your Seeed Studio XIAO microcontroller, you need to install two libraries via the Arduino IDE.

1. Open the Arduino IDE.
2. Go to **Sketch** > **Include Library** > **Manage Libraries...** (or press `Ctrl+Shift+I`).
3. In the search bar, search for and install:
   * **ArduinoBLE** (by Arduino)
   * **LSM6DS3** (by Seeed Studio)
4. Select your specific XIAO board and the correct COM port, then click **Upload**.
