import sys
import socket
import threading
import numpy as np
import cv2
import time
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                             QVBoxLayout, QPushButton, QFrame)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import pyqtSignal, Qt, QTimer

# =========================
# CONFIG
# =========================
TCP_PORT = 9999
UDP_PORT = 9998  # For discovery
BROADCAST_MSG = b"CBT_MONITOR_SERVER_ACTIVE"

class StudentWidget(QFrame):
    def __init__(self, pc_name, parent_dashboard):
        super().__init__()
        self.pc_name = pc_name
        self.parent_dashboard = parent_dashboard
        self.setStyleSheet("""
            StudentWidget { background-color: #2b2b2b; border: 2px solid #3d3d3d; border-radius: 8px; }
            QLabel { color: #ffffff; border: none; }
        """)
        layout = QVBoxLayout(self)
        self.name_label = QLabel(f"🖥️ PC: {pc_name}")
        self.name_label.setStyleSheet("font-weight: bold; color: #00ff00;")
        layout.addWidget(self.name_label)
        self.screen_label = QLabel("Waiting for Stream...")
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setStyleSheet("background-color: black; border-radius: 4px;")
        self.screen_label.setMinimumSize(320, 180)
        layout.addWidget(self.screen_label)
        self.btn_screenshot = QPushButton("📸 Capture Screenshot")
        self.btn_screenshot.setStyleSheet("background-color: #444; color: white; border-radius: 4px; padding: 6px;")
        self.btn_screenshot.clicked.connect(self.take_screenshot)
        layout.addWidget(self.btn_screenshot)
        self.screen_label.mouseDoubleClickEvent = lambda e: self.parent_dashboard.toggle_student_focus(self)

    def take_screenshot(self):
        pixmap = self.screen_label.pixmap()
        if pixmap:
            if not os.path.exists("screenshots"): os.makedirs("screenshots")
            filename = f"screenshots/{self.pc_name}_{time.strftime('%H%M%S')}.jpg"
            pixmap.save(filename, "JPG")
            self.setStyleSheet("background-color: #1a472a; border: 2px solid green; border-radius: 8px;")
            QTimer.singleShot(500, lambda: self.setStyleSheet("background-color: #2b2b2b; border: 2px solid #3d3d3d; border-radius: 8px;"))

class Dashboard(QWidget):
    update_signal = pyqtSignal(object, object)
    new_client_signal = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instructor Dashboard")
        self.resize(1100, 800)
        self.setStyleSheet("background-color: #111;")
        self.grid_layout = QGridLayout(self)
        self.students = {}
        self.focused_student = None
        self.update_signal.connect(self.update_frame)
        self.new_client_signal.connect(self.add_student_widget)

    def add_student_widget(self, pc_name, result_dict):
        widget = StudentWidget(pc_name, self)
        index = len(self.students)
        self.grid_layout.addWidget(widget, index // 3, index % 3)
        self.students[pc_name] = widget
        result_dict['widget'] = widget

    def toggle_student_focus(self, widget):
        if self.focused_student is None:
            for w in self.students.values(): 
                if w != widget: w.hide()
            self.grid_layout.removeWidget(widget)
            self.grid_layout.addWidget(widget, 0, 0)
            widget.screen_label.setMinimumSize(960, 540)
            self.focused_student = widget
        else:
            self.focused_student = None
            widget.screen_label.setMinimumSize(320, 180)
            for i, w in enumerate(self.students.values()):
                self.grid_layout.addWidget(w, i // 3, i % 3)
                w.show()

    def update_frame(self, widget, frame):
        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            q_img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            lbl = widget.screen_label
            lbl.setPixmap(pixmap.scaled(lbl.width(), lbl.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except: pass

# --- AUTO-DISCOVERY BROADCASTER ---
def broadcast_identity():
    """Tells the network where the instructor is every 3 seconds."""
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print(f"[*] Discovery Broadcaster started on UDP {UDP_PORT}...")
    while True:
        try:
            broadcaster.sendto(BROADCAST_MSG, ('<broadcast>', UDP_PORT))
        except: pass
        time.sleep(3)

def recv_all(conn, n):
    data = b''
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def handle_client(conn, addr, dashboard):
    try:
        name_len_data = conn.recv(1)
        if not name_len_data: return
        pc_name = conn.recv(int.from_bytes(name_len_data, 'big')).decode('utf-8')
        res = {'widget': None}
        dashboard.new_client_signal.emit(pc_name, res)
        while res['widget'] is None: time.sleep(0.1)
        widget = res['widget']
        while True:
            size_data = recv_all(conn, 4)
            if not size_data: break
            frame_data = recv_all(conn, int.from_bytes(size_data, 'big'))
            if not frame_data: break
            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None: dashboard.update_signal.emit(widget, frame)
    except: pass
    finally: conn.close()

def start_server(dashboard):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", TCP_PORT))
    server.listen(20)
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr, dashboard), daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dash = Dashboard()
    dash.show()
    threading.Thread(target=broadcast_identity, daemon=True).start()
    threading.Thread(target=start_server, args=(dash,), daemon=True).start()
    sys.exit(app.exec())