from io import BytesIO
import os
import cv2
import numpy as np
import serial
import time
from pyzbar import pyzbar
import threading

# Specify the path to ffmpeg and ffprobe executables
ffmpeg_path = "C:\\Users\\hello\\Downloads\\ffmpeg-master-latest-win64-gpl\\ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe"
ffprobe_path = "C:\\Users\\hello\\Downloads\\ffmpeg-master-latest-win64-gpl\\ffmpeg-master-latest-win64-gpl\\bin\\ffprobe.exe"

# Set the PATH environment variable in the script
os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)

# Check if the ffmpeg and ffprobe paths are correct
if not os.path.isfile(ffmpeg_path):
    raise FileNotFoundError(f"ffmpeg executable not found at {ffmpeg_path}")

if not os.path.isfile(ffprobe_path):
    raise FileNotFoundError(f"ffprobe executable not found at {ffprobe_path}")

AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path



def speak_text(text, speed=1.0):
    tts = gTTS(text=text, lang='en')
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    audio = AudioSegment.from_file(audio_fp, format="mp3")

    # Adjust the playback speed
    if speed != 1.0:
        audio = audio.speedup(playback_speed=speed)

    play(audio)


speak_text("Sure, Let me take you to the manager's office. Please follow me")


# Thread class for serial communication
class SerialThread(threading.Thread):
    def __init__(self):
        super(SerialThread, self).__init__()
        self.lock = threading.Lock()
        self.running = True
        self.command = None
        try:
            self.ser = serial.Serial('COM7', 115200, timeout=.025, write_timeout=.025)  # Adjust to your Arduino's serial port
            time.sleep(2)  # Allow time for serial connection to establish
        except serial.SerialException as e:
            print(f"Error: {e}")
            exit()

    def run(self):
        while self.running:
            if self.command:
                with self.lock:
                    command_to_send = self.command
                    self.command = None
                try:
                    if self.ser.isOpen():
                        self.ser.write(command_to_send.encode())  # Send the command to the Arduino
                        self.ser.flush()  # Ensure all data is sent immediately
                    else:
                        print("Serial port is not open.")
                except serial.SerialException as e:
                    try:
                        self.ser.close()
                        self.ser = serial.Serial('COM7', 115200, timeout=.025, write_timeout=.025)  # Adjust to your Arduino's serial port
                        time.sleep(2)  # Allow time for serial connection to establish
                    except serial.SerialException as e:
                        print(f"Retry Error: {e}")
                    print(f"Serial communication error: {e}")
            time.sleep(0.025)  # Adjust sleep time as needed

    def send_command(self, command):
        with self.lock:
            self.command = command

    def stop(self):
        self.running = False
        self.ser.close()

serial_thread = SerialThread()

# Function to send motor commands
def send_wheel_command(left_speed, right_speed):
    command = f"MOVE {left_speed} {right_speed}\n"
    print(f"Sending command: {command.strip()}")
    serial_thread.send_command(command)

# Function to find the path and return its contour
def find_path(hsv):
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([200, 255, 70])
    mask = cv2.inRange(hsv, lower_black, upper_black)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    biggest = None
    biggest_size = -1
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > biggest_size:
            biggest = contour
            biggest_size = area
    return biggest

# Function to detect lines and calculate control signals
def detect_lines(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    contour = find_path(hsv)
    mask = np.zeros_like(hsv[:, :, 0])
    if contour is not None:
        cv2.drawContours(mask, [contour], -1, 255, -1)
        mask = cv2.medianBlur(mask, 5)
    res = cv2.bitwise_and(image, image, mask=mask)
    copy = image.copy()
    line_detected = False
    if contour is not None:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            cv2.line(image, (cx, 0), (cx, 720), (255, 0, 0), 1)
            cv2.line(image, (0, cy), (1280, cy), (255, 0, 0), 1)
            cv2.drawContours(copy, [contour], -1, (0, 255, 0), 1)
            print(cx)
            if 45 < cx < 80:
                send_wheel_command(3, -3)  # Move forward
            elif cx <= 45:
                send_wheel_command(-4.5, -4.5)  # Turn left
            elif cx >= 190:
                send_wheel_command(4.5, 4.5)  # Turn right

            line_detected = True
    return image, copy, hsv, res, line_detected    

# Function to decode QR codes
def decode_qr_code(frame, last_detected_time, cooldown, allow_detection):
    if not allow_detection:
        return frame, False, 0, last_detected_time

    qr_codes = pyzbar.decode(frame)
    stop_robot = False
    stop_duration = 0
    current_time = time.time()
    if current_time - last_detected_time < cooldown:
        return frame, stop_robot, stop_duration, last_detected_time  # Return without processing if within cooldown

    for qr_code in qr_codes:
        (x, y, w, h) = qr_code.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        qr_data = qr_code.data.decode('utf-8')
        qr_type = qr_code.type
        text = f"{qr_data} ({qr_type})"
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        print(f"Decoded QR code: {qr_data}")
        if qr_data == "Station":
            print("Detected QR code 'initial location'. Stopping robot.")
            stop_robot = True
            stop_duration = float('inf')  # Stop indefinitely
            last_detected_time = current_time
        elif qr_data == "Manager's Office":
            print("Detected QR code 'gate A'. Pausing robot for 20 seconds.")
            speak_text("We have reached the manager's office. Thank you")
            stop_robot = True
            stop_duration = 10  # Pause for 20 seconds
            last_detected_time = current_time
    return frame, stop_robot, stop_duration, last_detected_time

# Thread class for video capture
class VideoCaptureThread(threading.Thread):
    def __init__(self, src=0):
        super(VideoCaptureThread, self).__init__()
        self.capture = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.capture.set(3, 300)
        self.capture.set(4, 300)
        self.lock = threading.Lock()
        self.running = True
        self.frame = None

    def run(self):
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                with self.lock:
                    self.frame = frame

    def read(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        self.capture.release()

# Thread class for frame processing
class FrameProcessingThread(threading.Thread):
    def __init__(self, video_thread):
        super(FrameProcessingThread, self).__init__()
        self.video_thread = video_thread
        self.running = True
        self.stop_robot = False
        self.stop_time = 0
        self.stop_duration = 0
        self.last_detected_time = 0
        self.qr_cooldown = 22  # Cooldown period in seconds
        self.allow_qr_detection = True

    def run(self):
        desired_fps = 10  # Adjust desired frames per second here
        delay = int(1000 / desired_fps)

        while self.running:
            frame = self.video_thread.read()
            if frame is None:
                continue

            # QR code detection
            try:
                frame, detected_qr_stop, stop_duration, self.last_detected_time = decode_qr_code(
                    frame, self.last_detected_time, self.qr_cooldown, self.allow_qr_detection)
            except Exception as e:
                print(f"Error in QR code decoding: {e}")
                continue

            if detected_qr_stop:
                self.stop_robot = True
                self.stop_time = time.time()
                self.stop_duration = stop_duration
                self.allow_qr_detection = False  # Disable further QR detection during the stop

            # Check if the robot should be stopped
            if self.stop_robot:
                elapsed_time = time.time() - self.stop_time
                if elapsed_time < self.stop_duration or self.stop_duration == float('inf'):
                    print("Stopping robot")
                    send_wheel_command(0, 0)
                    if stop_duration == 10 and elapsed_time == 0:  # To ensure the text is spoken only once when it stops
                        # speak_text("Here we are! This is your boarding gate. If you have any other questions or need further assistance, feel free to ask. Have a great flight")
                        cv2.imshow('QR Code Scanner', frame)
                    if cv2.waitKey(delay) & 0xFF == ord('q'):
                        self.running = False
                        break
                    continue  
                else:
                    print("Resuming robot movement")
                    send_wheel_command(-3, 3)  # Turn with the specified values
                    time.sleep(1.5)  # Robot turns for 1.5 seconds
                    send_wheel_command(0, 0)  # Stop the robot after turning
                    time.sleep(20)
                    self.stop_robot = False
                    self.allow_qr_detection = True  # Re-enable QR detection after resuming

            # Line following
            cropped = frame[100:250, 90:200]
            original, center, hsv, res, line_detected = detect_lines(cropped)

            # Display frames
            try:
                cv2.imshow('QR Code Scanner', frame)
                cv2.imshow('hsv', hsv)
                cv2.imshow('res', res)
                if center is not None:
                    cv2.imshow('Detected Lines', center)
                if original is not None:
                    cv2.imshow('Contours', original)
            except Exception as e:
                print(f"Error displaying frames: {e}")

            if not line_detected:
                print("No line detected. Sending stop command.")
                send_wheel_command(0, 0)

            if cv2.waitKey(delay) & 0xFF == ord('q'):
                self.running = False
                break

    def stop(self):
        self.running = False

def main():
    video_thread = VideoCaptureThread()  # Correct initialization

    processing_thread = FrameProcessingThread(video_thread)  # Pass video_thread to processing_thread
    serial_thread.start()  # Start the serial communication thread
    video_thread.start()
    processing_thread.start()

    try:
        while processing_thread.is_alive():
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        video_thread.stop()
        processing_thread.stop()
        serial_thread.stop()

    finally:
        video_thread.stop()
        processing_thread.stop()
        serial_thread.stop()

        video_thread.join()
        processing_thread.join()
        serial_thread.join()
        cv2.destroyAllWindows()
        serial_thread.ser.close()
        print("Serial connection closed.")

if __name__ == "__main__":
    main()