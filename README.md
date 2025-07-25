
This is a Flask-based web application that enables users to generate customized maps using natural language prompts, accompanied by a secure user login system.

<img width="975" height="524" alt="image" src="https://github.com/user-attachments/assets/d707fe4e-32a6-45b2-8ec5-7806163ecc93" />
Upload geojson data and start chat & mapping (USA, NYC and pakistan data is provided seprately)

<img width="975" height="211" alt="image" src="https://github.com/user-attachments/assets/0ca3e510-bf30-47e8-a059-bc0fcda2a7a2" />
<img width="975" height="66" alt="image" src="https://github.com/user-attachments/assets/d4549fc4-33f2-4631-b7a4-85e73bb783b0" />
<img width="975" height="635" alt="image" src="https://github.com/user-attachments/assets/0dd82de4-03d8-4b21-818f-7063984c42c7" />
<img width="975" height="252" alt="image" src="https://github.com/user-attachments/assets/06d93028-bc49-4ea5-bba3-4034c7272c8a" />
<img width="1086" height="174" alt="image" src="https://github.com/user-attachments/assets/02b5be74-499c-4aa3-bf6a-7f5c38ab0f8a" />
<img width="798" height="826" alt="image" src="https://github.com/user-attachments/assets/b5e0a53e-4e44-4978-bb17-0ab05ebd8db2" />
<img width="975" height="90" alt="image" src="https://github.com/user-attachments/assets/947fa799-cf00-4ed1-8397-8df945c197ba" />
<img width="975" height="74" alt="image" src="https://github.com/user-attachments/assets/e7808b6d-c529-4447-9d08-0ade2937b5ed" />
<img width="966" height="1033" alt="image" src="https://github.com/user-attachments/assets/e200d256-47ce-41f4-9bf6-d23f80ac5320" />





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

