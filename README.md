# MapChatterbot
This is a Flask-based web application that enables users to generate customized maps using natural language prompts, accompanied by a secure user login system.

<img width="975" height="524" alt="image" src="https://github.com/user-attachments/assets/d707fe4e-32a6-45b2-8ec5-7806163ecc93" />

🌟 Features

- 🔐 **User Login System** (Session-based authentication)
- 🧠 **AI-based Prompt Understanding**
- 🗺️ **Dynamic Map Generation** with Folium
- 🎨 **Custom Legend Position, Size, and Color Scheme**
- 🌐 **Clean Web Interface (HTML/CSS/JS)**
- 🤖 **Gemini API-Ready via `.env`**

1️⃣ Clone the Repository

git clone https://github.com/mabdullahbaig/MapChatterbot.git
cd AI-Powered-mapping-webApp

2️⃣ Create a Virtual Environment

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

3️⃣ Install Requirements

pip install -r requirements.txt

4️⃣ Set Up Environment Variables
Create a .env file in the root directory:

GEMINI_API_KEY=your_gemini_api_key_here

5️⃣ Run the App

python run.py
Visit: http://127.0.0.1:5000

