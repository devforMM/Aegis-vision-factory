import cv2
import pandas as pd
import torch
from ultralytics import YOLO

# ==============================================================================
# HARDWARE CONFIGURATION
# ==============================================================================

# Select CUDA if a GPU is available, otherwise fallback to CPU
device = "cuda" if torch.cuda.is_available() else "cpu"


# ==============================================================================
# MODEL INITIALIZATION
# ==============================================================================

def get_models():
    """
    Loads the custom pre-trained YOLO models from the disk 
    and transfers them to the selected hardware acceleration device (GPU/CPU).
    
    Returns:
        dict: A dictionary containing the instantiated YOLO models.
    """
    fire_model = YOLO("deep_learning/fire_model.pt").to(device)
    ppe_model = YOLO("deep_learning/ppe_model.pt").to(device)
    
    return {
        "fire_model": fire_model,
        "ppe_model": ppe_model
    }


# ==============================================================================
# INFERENCE & PREDICTION
# ==============================================================================

def model_prediction(model, image, result_image_path):
    """
    Runs object detection on a single frame/image using a specific YOLO model.
    Saves the annotated visual output to the disk and returns the detected classes.
    
    Args:
        model: The loaded YOLO model instance.
        image: The input image matrix (NumPy array from OpenCV or file path).
        result_image_path (str): File path where the annotated image will be saved.
        
    Returns:
        list: A list of strings representing the names of all detected objects.
    """
    # Extract object class mapping defined in the model
    class_names = model.names
    
    # Perform object detection inference on the input image
    results = model(image)[0]
    
    # Map class IDs from the detection boxes to their corresponding text labels
    detected_classes = [class_names[int(c)] for c in results[0].boxes.cls]
    
    # Save the visual result containing bounding boxes and labels to the disk
    results.save(filename=result_image_path)
    
    return detected_classes