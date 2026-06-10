from ultralytics import YOLO
import os

if __name__ == '__main__':
    # 1. Define the absolute path to your downloaded yaml configuration
    dataset_yaml_path = os.path.abspath("data.yaml")

    # 2. Load the base YOLOv8 Nano model
    model = YOLO("yolov8n.pt") 

    # 3. Train the model
    print("Starting training...")
    results = model.train(
        data=dataset_yaml_path,
        epochs=50,          
        imgsz=640,          
        device=0,           
        workers=4           
    )

    # 4. Export the newly trained weights directly to the ARM-friendly NCNN format
    print("Training complete. Exporting to NCNN...")
    model.export(format="ncnn")