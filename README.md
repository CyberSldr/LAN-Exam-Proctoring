# LAN Exam Proctoring System 🖥️🛡️

A real-time, lightweight proctoring solution designed for local area networks (LAN). This system allows an instructor to monitor multiple student screens simultaneously without manual IP configuration.

## ✨ Features
- **Zero Configuration:** Uses UDP Broadcasting to automatically find the instructor's dashboard on the network.
- **Multi-Interface Support:** Works across WiFi, Ethernet, and Virtual Adapters (VMWare/VirtualBox).
- **Live Monitoring:** Real-time screen streaming via OpenCV.
- **Evidence Collection:** One-click screenshots saved with the student's PC name and timestamp.
- **Focus Mode:** Double-click any student feed to toggle between gallery view and full-screen focus.
- **Identity Burn-in:** Student PC names are overlaid directly onto the video feed for easier identification.

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- All devices must be on the same local network (LAN)


### Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/CyberSldr/LAN-Exam-Proctoring.git](https://github.com/CyberSldr/LAN-Exam-Proctoring.git)
   cd LAN-Exam-Proctoring
   pip install -r requirements.txt
   python3 Instr_dashboard.py # Run on the instructor PC
   python3 Stu_client.py # Run on the students/clients PC
