import cv2
from ultralytics import YOLO

# 1. Load your original trained PyTorch model for the PC test
# We use the .pt file here since your PC can run it natively with its GPU
model_path = "/home/Isaac_Muni/Documents/Robótica_2/Final/runs/detect/train-5/weights/best.pt"
model = YOLO(model_path) 

# 2. Initialize your computer's standard webcam (usually index 0)
cap = cv2.VideoCapture(0)

print("Starting PC webcam test. Press 'q' inside the video window to quit.")

while True:
    # Capture the frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from webcam. Is it plugged in and accessible?")
        break

    # 3. Run inference on the frame
    # By default, YOLOv8 will use your RTX 4050 if the environment is still active
    results = model(frame, stream=True)

    for r in results:
        # The .plot() function automatically draws the bounding boxes, 
        # labels, and confidence scores directly onto the frame
        annotated_frame = r.plot()
        
        # 4. Display the resulting frame in a new window
        cv2.imshow("Model Training Test (Stairs & Crosswalks)", annotated_frame)

    # Listen for the 'q' key to close the program gracefully
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up the webcam and destroy the window
cap.release()
cv2.destroyAllWindows()