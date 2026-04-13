import socket
import cv2
import numpy as np
import mss
import time
import platform

# =========================
# CONFIG
# =========================
UDP_PORT = 9998
TCP_PORT = 9999
BROADCAST_MSG = b"CBT_MONITOR_SERVER_ACTIVE"

def find_instructor_ip():
    """Listens for the instructor's broadcast signal."""
    print("[*] Searching for Instructor Dashboard on the network...")
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(("", UDP_PORT))
    
    while True:
        data, addr = client.recvfrom(1024)
        if data == BROADCAST_MSG:
            print(f"[+] Instructor found at: {addr[0]}")
            client.close()
            return addr[0]

def start_student_client():
    # Step 1: Discover the Instructor automatically
    server_ip = find_instructor_ip()
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, TCP_PORT))
        pc_name = platform.node()
        name_bytes = pc_name.encode('utf-8')
        client_socket.sendall(len(name_bytes).to_bytes(1, 'big') + name_bytes)
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        return

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                img = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                frame = cv2.resize(frame, (640, 360))
                
                # Draw PC Name on frame
                cv2.rectangle(frame, (5, 330), (200, 355), (0, 0, 0), -1)
                cv2.putText(frame, f"PC: {pc_name}", (10, 350), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                data = buffer.tobytes()
                client_socket.sendall(len(data).to_bytes(4, 'big') + data)
                time.sleep(0.1)
            except:
                print("[-] Disconnected from Dashboard.")
                break
    client_socket.close()

if __name__ == "__main__":
    while True: # Keep trying to find the instructor if connection drops
        start_student_client()
        print("[*] Retrying discovery in 5 seconds...")
        time.sleep(5)