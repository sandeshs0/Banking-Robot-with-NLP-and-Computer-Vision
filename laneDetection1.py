import cv2
import numpy as np
import serial
import time
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk

# Initialize serial communication with Arduino
try:
    arduino = serial.Serial(port='COM5', baudrate=115200, timeout=1)
    time.sleep(2)  # Wait for the serial connection to initialize
except Exception as e:
    print(f"Error initializing serial communication: {e}")
    arduino = None

def send_command(command):
    if arduino is not None:
        try:
            arduino.write(f"{command}\n".encode())
            time.sleep(0.1)
            while arduino.inWaiting():
                print(arduino.readline().decode().strip())
        except Exception as e:
            print(f"Error sending command: {e}")

def process_frame(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Apply Canny edge detector
    edges = cv2.Canny(blur, 50, 150)
    return edges

def detect_lanes(edges):
    # Define region of interest (ROI)
    height, width = edges.shape
    mask = np.zeros_like(edges)
    polygon = np.array([[
        (0, height),
        (width, height),
        (width, height // 2),
        (0, height // 2)
    ]], np.int32)
    cv2.fillPoly(mask, polygon, 255)
    cropped_edges = cv2.bitwise_and(edges, mask)

    # Detect lines using Hough Transform
    lines = cv2.HoughLinesP(cropped_edges, 1, np.pi / 180, 50, maxLineGap=50)
    return lines

def compute_direction(lines):
    if lines is None:
        return "STOP"

    left_lines = []
    right_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        slope = (y2 - y1) / (x2 - x1) if (x2 - x1) != 0 else 0
        if slope < 0:
            left_lines.append(line)
        else:
            right_lines.append(line)

    if not left_lines and not right_lines:
        return "STOP"

    if len(left_lines) > len(right_lines):
        return "LEFT"
    elif len(right_lines) > len(left_lines):
        return "RIGHT"
    else:
        return "FORWARD"

def update_frame():
    ret, frame = cap.read()
    if ret:
        edges = process_frame(frame)
        lines = detect_lanes(edges)
        direction = compute_direction(lines)

        if direction == "FORWARD":
            send_command("MOVE 1500 1500")  # Send MOVE command to Arduino
        elif direction == "LEFT":
            send_command("MOVE 1200 1500")  # Send MOVE command to Arduino
        elif direction == "RIGHT":
            send_command("MOVE 1500 1200")  # Send MOVE command to Arduino
        else:
            send_command("MOVE 1500 1500")  # Stop the robot

        # Convert the image to RGB (OpenCV uses BGR by default)
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        # Display edges as well
        edges_img = Image.fromarray(edges)
        edges_imgtk = ImageTk.PhotoImage(image=edges_img)
        edges_label.imgtk = edges_imgtk
        edges_label.configure(image=edges_imgtk)

    root.after(10, update_frame)

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture")
        exit()

    # Set up the GUI
    root = tk.Tk()
    root.title("Robot Lane Detection")

    label = Label(root)
    label.pack(side="left")

    edges_label = Label(root)
    edges_label.pack(side="right")

    # Start the video loop
    update_frame()
    root.mainloop()

    cap.release()
    cv2.destroyAllWindows()
