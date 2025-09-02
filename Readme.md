# 🌀 CPU Fan Data Exfiltration Detection

**Cybersecurity Project | Flask + OpenCV + FFT**

This project demonstrates how **covert hardware channels** (like CPU fan speed variations) can be exploited for data exfiltration — and how such activity can be detected using **video analysis and signal processing**.

Attackers can modulate CPU fan speeds (using PWM) to encode binary data (`0` and `1`), which can then be captured by external sensors like cameras. Our system analyzes uploaded fan videos, extracts potential bitstreams, and attempts to reconstruct any hidden message.

---

## 🚀 Features
- 🎥 Upload fan videos through a web interface  
- 🔍 Video analysis with **OpenCV** (frame brightness tracking)  
- 📈 Frequency analysis using **FFT (Fast Fourier Transform)**  
- 🧮 Bitstream extraction & message decoding  
- 📊 Automated visualizations:
  - Brightness over time  
  - RPM variations  
  - FFT spectrum  
  - Extracted bitstream display  
- 📑 Downloadable analysis report (`.txt`)  

---

## 🛠️ Tech Stack
- **Backend**: Python, Flask  
- **Frontend**: HTML, CSS, JavaScript  
- **Video Processing**: OpenCV  
- **Signal Analysis**: NumPy, Matplotlib  
- **Reporting**: Auto-generated text file  

---

## 📂 Project Structure
fan-exfiltration-detection/
├── app.py # Main Flask app
├── ml_model/ # ML model scripts
│ └── ml_model.py
├── uploads/ # Uploaded videos + results
├── templates/
│ └── index.html # Web interface
├── static/
│ ├── css/style.css # Styles
│ └── js/script.js # Frontend logic
├── requirements.txt # Dependencies
├── Dockerfile # Docker setup
├── docker-compose.yml # Docker config
└── Readme.md # Documentation

yaml
Copy code

---

## ⚡ Quick Start

1. Clone this repository  
   ```bash
   git clone https://github.com/your-username/data-exfiltration-detection.git
   cd data-exfiltration-detection
Create and activate a virtual environment

bash
Copy code
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate # On Mac/Linux
Install dependencies

bash
Copy code
pip install -r requirements.txt
Run the application

bash
Copy code
python app.py
Open browser → http://127.0.0.1:5000

📖 How It Works
Upload Video → provide a clear video of a CPU fan

Brightness Analysis → system calculates frame brightness in a region of interest

FFT Processing → detects fan RPM frequency patterns

Bitstream Extraction → encodes binary data from RPM changes

Message Decoding → reconstructs hidden information

Report Generation → outputs summary + technical details

📚 Research Background
Inspired by works such as Fansmitter (Guri et al.) and SpiralSpy (Shamir et al.), this project shows that even simple hardware components like fans can become covert data exfiltration channels, bypassing firewalls and traditional defenses.

👨‍💻 Team
Gauri Kumar

Ritunjay Bhatt

Ansh Chauhan

Divyansh Pal

Sarthak Kumar Gupta

🔮 Future Scope
Real-world testing with live sensors (microphones/photodiodes)

Smarter anomaly detection using advanced signal analysis

Export reports as PDF with charts

Deployment on free cloud platforms (Render/Heroku)

⭐ If you find this project interesting, don’t forget to star it on GitHub!

yaml
Copy code

---

# 🔹 4. Push Changes to GitHub
Once `.gitignore` and `README.md` are ready:

```powershell
git init
git add .
git commit -m "Setup project with virtual environment, gitignore, and updated README"
git branch -M main
git remote add origin https://github.com/your-username/data-exfiltration-detection.git
git push -u origin main