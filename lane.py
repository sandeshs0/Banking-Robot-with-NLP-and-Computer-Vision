import cv2
import numpy as np
import serial
import time

# Configure the serial port (adjust the port as needed)
try:
    ser = serial.Serial('COM3', 115200)  # Use 'COM5' as per the image
    print("Serial connection established")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# Give some time to establish the serial connection
time.sleep(2)

# Function to send PWM command
def send_wheel_command(move1, move2):
    command = f"MOVE {move1} {move2}\n"
    print(f"Sending command: {command.strip()}")
    ser.write(command.encode())  # Send the command to the Arduino

# Capture video from the camera
cap = cv2.VideoCapture(0)  # Use the appropriate camera index

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Perform edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Define a region of interest
    height, width = edges.shape
    mask = np.zeros_like(edges)
    roi = np.array([[
        (0, height),
        (width // 2, height // 2),
        (width, height)
    ]], dtype=np.int32)
    cv2.fillPoly(mask, roi, 255)
    masked_edges = cv2.bitwise_and(edges, mask)

    # Find the contours in the edged image
    contours, _ = cv2.findContours(masked_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            # Draw the largest contour and its centroid
            cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

            # Determine the error from the center of the frame
            error = cx - width // 2

            # Control logic to follow the line
            if error > 20:
                send_wheel_command(50, -50)  # Turn right
            elif error < -20:
                send_wheel_command(-50, 50)  # Turn left
            else:
                send_wheel_command(50, 50)  # Move forward
        else:
            send_wheel_command(0, 0)  # Stop if no line is detected
    else:
        send_wheel_command(0, 0)  # Stop if no line is detected

    # Display the frame
    cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the serial connection
cap.release()
ser.close()
cv2.destroyAllWindows()
print("Serial connection closed.")
