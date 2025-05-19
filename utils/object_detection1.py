import os
import yaml
import shutil
import argparse
import logging
import requests
import time
import numpy as np
import cv2
from zipfile import ZipFile
from tqdm import tqdm
from PIL import Image
from typing import List, Dict, Tuple, Optional, Union
from ultralytics import YOLO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("waste_detector")

class WasteDetector:
    """A comprehensive waste bin and object detection system using YOLOv8."""
    
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.25):
        """
        Initialize the waste detector.
        
        Args:
            model_path: Path to the YOLO model file
            conf_threshold: Confidence threshold for detections
        """
        self.conf_threshold = conf_threshold
        try:
            start_time = time.time()
            self.model = YOLO(model_path)
            logger.info(f"Model loaded in {time.time() - start_time:.2f} seconds")

            # Define waste-related classes for standard COCO model
            self.waste_related_classes = {
                'bottle', 'cup', 'bowl', 'chair', 'suitcase', 'backpack',
                'potted plant', 'dining table', 'toilet', 'tv', 'microwave', 
                'oven', 'refrigerator', 'vase', 'scissors', 'teddy bear'
            }
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def pre_process(self, image: np.ndarray) -> np.ndarray:
        """
        Pre-process the image to improve detection in challenging conditions.
        
        Args:
            image: OpenCV BGR image
            
        Returns:
            Processed image
        """
        # Convert to RGB for processing
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply contrast limited adaptive histogram equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Convert to LAB color space
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L-channel
        l_clahe = clahe.apply(l)
        
        # Merge back the channels
        lab = cv2.merge((l_clahe, a, b))
        
        # Convert back to RGB
        processed = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        # Convert back to BGR for OpenCV operations
        return cv2.cvtColor(processed, cv2.COLOR_RGB2BGR)

    def detect(self, 
               image: Union[str, np.ndarray, Image.Image], 
               visualize: bool = True,
               apply_preprocessing: bool = True
              ) -> Tuple[Optional[Image.Image], List[Dict]]:
        """
        Detect waste objects in an image.
        
        Args:
            image: Input image (file path, numpy array, or PIL Image)
            visualize: Whether to draw bounding boxes on the image
            apply_preprocessing: Whether to apply image preprocessing
            
        Returns:
            Tuple of (annotated image if visualize=True else None, list of detection results)
        """
        try:
            # Handle different input types
            if isinstance(image, str):
                if not os.path.exists(image):
                    raise FileNotFoundError(f"Image file not found: {image}")
                image = Image.open(image)
                
            # Convert PIL image to numpy array if needed
            if isinstance(image, Image.Image):
                opencv_image = np.array(image)
                opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)
            else:
                opencv_image = image.copy()
                
            # Apply preprocessing if enabled
            if apply_preprocessing:
                opencv_image = self.pre_process(opencv_image)
                
            # Perform object detection
            start_time = time.time()
            results = self.model.predict(
                opencv_image, 
                conf=self.conf_threshold,
                verbose=False
            )
            inference_time = time.time() - start_time
            logger.debug(f"Detection completed in {inference_time:.4f} seconds")
            
            # Extract detection results
            detected_objects = []
            result = results[0]
            boxes = result.boxes
            
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = result.names[cls]
                
                # Calculate center point and dimensions
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                width = x2 - x1
                height = y2 - y1
                
                # Check if this object might be a waste bin if not explicitly labeled
                is_waste_bin = False
                if class_name.lower() in ['bin', 'trash', 'garbage', 'container', 'dumpster']:
                    is_waste_bin = True
                # If object has waste bin-like aspect ratio (typically taller than wide)
                elif 0.7 <= height/width <= 3.0:
                    # This is a heuristic to identify potential unlabeled waste bins
                    # We could add color analysis here for better recognition
                    is_waste_bin = True
                
                detection_info = {
                    'id': i,
                    'name': class_name,
                    'confidence': round(conf * 100, 2),  # convert to percentage
                    'bbox': {
                        'x1': x1, 
                        'y1': y1, 
                        'x2': x2, 
                        'y2': y2
                    },
                    'center': {
                        'x': center_x,
                        'y': center_y
                    },
                    'dimensions': {
                        'width': width,
                        'height': height
                    },
                    'is_potential_waste_bin': is_waste_bin
                }
                detected_objects.append(detection_info)
                
                # Draw bounding box if visualization is enabled
                if visualize:
                    # Generate a unique color
                    color = self._get_color_for_class(cls)
                    
                    # Use different color for potential waste bins
                    if is_waste_bin and class_name.lower() not in ['bin', 'trash', 'garbage', 'container', 'dumpster']:
                        color = (0, 165, 255)  # Orange for potential waste bins
                        
                    # Draw bounding box
                    cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw filled background for text
                    display_name = class_name
                    if is_waste_bin and class_name.lower() not in ['bin', 'trash', 'garbage', 'container', 'dumpster']:
                        display_name = f"{class_name} (Possible Bin)"
                        
                    text = f"{display_name} {conf:.2f}"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(
                        opencv_image, 
                        (x1, y1 - text_size[1] - 10),
                        (x1 + text_size[0], y1), 
                        color, 
                        -1
                    )
                    
                    # Draw text with better contrast
                    cv2.putText(
                        opencv_image,
                        text,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),  # White text for better contrast
                        2
                    )
            
            # Convert back to PIL image if visualization was requested
            if visualize:
                detected_image = Image.fromarray(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB))
                return detected_image, detected_objects
            else:
                return None, detected_objects
                
        except Exception as e:
            logger.error(f"Error during detection: {e}")
            raise

    def _get_color_for_class(self, class_id: int) -> Tuple[int, int, int]:
        """Generate a consistent color for a class ID."""
        colors = [
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 0, 0),    # Blue
            (0, 255, 255),  # Yellow
            (255, 0, 255),  # Magenta
            (255, 255, 0),  # Cyan
            (128, 0, 0),    # Dark blue
            (0, 128, 0),    # Dark green
            (0, 0, 128),    # Dark red
            (128, 128, 0),  # Olive
        ]
        return colors[class_id % len(colors)]
    
    def process_video(self, 
                     video_path: str, 
                     output_path: Optional[str] = None,
                     display: bool = False,
                     skip_frames: int = 0
                    ) -> None:
        """
        Process a video file for waste object detection.
        
        Args:
            video_path: Path to input video file
            output_path: Path to save the output video (None to skip saving)
            display: Whether to display video while processing
            skip_frames: Number of frames to skip for faster processing
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Initialize video writer if output path is specified
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        processing_start = time.time()
        
        try:
            # Process the video frame by frame
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1
                
                # Skip frames if requested (for faster processing)
                if skip_frames > 0 and frame_count % (skip_frames + 1) != 0:
                    if writer:
                        writer.write(frame)
                    continue
                
                # Show progress
                if frame_count % 10 == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"Processing: {progress:.1f}% - Frame {frame_count}/{total_frames}")
                
                # Detect objects in the frame
                detected_frame, detections = self.detect(frame, visualize=True)
                
                # Convert PIL image back to OpenCV format
                opencv_frame = cv2.cvtColor(np.array(detected_frame), cv2.COLOR_RGB2BGR)
                
                # Write frame to output video if specified
                if writer:
                    writer.write(opencv_frame)
                    
                # Display frame if requested
                if display:
                    cv2.imshow('Waste Detection', opencv_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise
            
        finally:
            # Clean up resources
            if writer:
                writer.release()
            cap.release()
            cv2.destroyAllWindows()
            
            # Print summary
            elapsed = time.time() - processing_start
            logger.info(f"Video processing complete: {frame_count} frames in {elapsed:.2f} seconds")
            if output_path:
                logger.info(f"Output saved to: {output_path}")

# Dataset handling functions
def download_file(url, destination):
    """
    Download a file with progress bar
    
    Args:
        url: URL to download from
        destination: Local path to save the file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    # Make request
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Show download progress
    with open(destination, 'wb') as file, tqdm(
        desc=os.path.basename(destination),
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)
    
    return destination

def extract_zip(zip_path, extract_to):
    """Extract a zip file to the specified directory."""
    os.makedirs(extract_to, exist_ok=True)
    
    with ZipFile(zip_path, 'r') as zip_ref:
        total = len(zip_ref.infolist())
        for file in tqdm(zip_ref.infolist(), total=total, desc="Extracting"):
            zip_ref.extract(file, extract_to)
    
    return extract_to

def download_waste_dataset(dataset_name, output_dir):
    """
    Download a waste detection dataset
    
    Args:
        dataset_name: Name of the dataset to download ('waste-roboflow', 'taco', or 'custom-url')
        output_dir: Directory to save the dataset
    
    Returns:
        Path to the dataset directory
    """
    dataset_dir = os.path.join(output_dir, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)
    
    if dataset_name.lower() == 'waste-roboflow':
        # Download Waste Dataset from Roboflow
        print("Downloading Waste Detection dataset from Roboflow...")
        
        # Direct link to Roboflow dataset (example URL - you'll need to get your own for production)
        dataset_url = "https://app.roboflow.com/ds/YOUR_DATASET_KEY?key=YOUR_API_KEY"
        
        print("Note: You'll need to get your own API key from Roboflow to download this dataset.")
        print("Visit https://app.roboflow.com/ to sign up and get access.")
        
        # Instructions to download dataset
        print("\nAlternatively, you can download the dataset manually and place it in:")
        print(f"{dataset_dir}/train/images")
        print(f"{dataset_dir}/train/labels")
        print(f"{dataset_dir}/valid/images")
        print(f"{dataset_dir}/valid/labels")
        
        return dataset_dir
        
    elif dataset_name.lower() == 'taco':
        # Download TACO dataset (Trash Annotations in Context)
        print("Downloading TACO dataset...")
        taco_url = "https://github.com/pedropro/TACO/archive/refs/heads/master.zip"
        zip_path = os.path.join(dataset_dir, "taco.zip")
        download_file(taco_url, zip_path)
        extract_zip(zip_path, dataset_dir)
        
        print("TACO dataset downloaded. Note: This dataset needs conversion to YOLO format.")
        print("You'll need to convert the annotations using a script like labelme2yolo or coco2yolo.")
        
        return dataset_dir
        
    elif dataset_name.lower() == 'custom-url':
        # Custom dataset URL
        custom_url = input("Enter the direct URL to your dataset ZIP file: ")
        print(f"Downloading dataset from {custom_url}...")
        
        zip_path = os.path.join(dataset_dir, "dataset.zip")
        download_file(custom_url, zip_path)
        extract_zip(zip_path, dataset_dir)
        
        print("Custom dataset downloaded.")
        return dataset_dir
    
    else:
        raise ValueError(f"Unknown dataset name: {dataset_name}")

def create_data_yaml(dataset_path):
    """
    Create a YAML file for training with waste container classes.
    
    Args:
        dataset_path: Path to dataset directory
    
    Returns:
        Path to created YAML file
    """
    # Define waste container classes
    waste_classes = [
        'waste_bin',        # Standard trash bins
        'recycling_bin',    # Recycling containers
        'dumpster',         # Large waste containers
        'compost_bin',      # Organic waste bins
        'ewaste_bin'        # Electronic waste bins
    ]
    
    # Define paths
    train_path = os.path.join(dataset_path, 'train')
    val_path = os.path.join(dataset_path, 'val')
    
    # Check if the expected directory structure exists
    if not os.path.exists(train_path):
        os.makedirs(train_path, exist_ok=True)
        print(f"Created training directory: {train_path}")
        print("You need to add training images in train/images and labels in train/labels")
    
    if not os.path.exists(val_path):
        os.makedirs(val_path, exist_ok=True)
        print(f"Created validation directory: {val_path}")
        print("You need to add validation images in val/images and labels in val/labels")
    
    # Create data.yaml content
    data = {
        'path': dataset_path,
        'train': train_path,
        'val': val_path,
        'test': '',  # Optional test set
        'names': {i: name for i, name in enumerate(waste_classes)},
        'nc': len(waste_classes)
    }
    
    # Write YAML file
    yaml_path = os.path.join(dataset_path, 'waste_containers.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)
    
    print(f"Created dataset configuration at {yaml_path}")
    return yaml_path

def train_model(data_yaml, model_size='n', epochs=50, img_size=640, batch_size=16):
    """
    Train a YOLOv8 model on waste container dataset.
    
    Args:
        data_yaml: Path to data YAML file
        model_size: Model size ('n', 's', 'm', 'l')
        epochs: Number of training epochs
        img_size: Image size for training
        batch_size: Batch size
        
    Returns:
        Path to trained model
    """
    # Select model based on size
    if model_size == 'n':
        model_path = 'yolov8n.pt'
    elif model_size == 's':
        model_path = 'yolov8s.pt'
    elif model_size == 'm':
        model_path = 'yolov8m.pt'
    elif model_size == 'l':
        model_path = 'yolov8l.pt'
    else:
        model_path = 'yolov8n.pt'  # Default to nano
    
    # Load model
    model = YOLO(model_path)
    
    # Train model
    try:
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            name='waste_detector',
            patience=20,  # Early stopping
            device='0'    # Use GPU if available
        )
        
        # Find best model path
        best_model_path = os.path.join('runs', 'detect', 'waste_detector', 'weights', 'best.pt')
        
        if os.path.exists(best_model_path):
            print(f"Training complete! Best model saved to: {best_model_path}")
            return best_model_path
        else:
            last_model_path = os.path.join('runs', 'detect', 'waste_detector', 'weights', 'last.pt')
            print(f"Training complete! Last model saved to: {last_model_path}")
            return last_model_path
            
    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise

def main():
    """Main function to download dataset, train model, and run detection."""
    parser = argparse.ArgumentParser(description="Waste Container Detection System")
    parser.add_argument("--mode", choices=['download', 'train', 'detect', 'all'], default='detect',
                        help="Operation mode: download dataset, train model, or run detection")
    parser.add_argument("--dataset", type=str, default='waste-roboflow',
                        help="Dataset to download: waste-roboflow, taco, or custom-url")
    parser.add_argument("--dataset_dir", type=str, default='datasets',
                        help="Directory to save/load dataset")
    parser.add_argument("--model_size", choices=['n', 's', 'm', 'l'], default='n',
                        help="YOLOv8 model size: n (nano), s (small), m (medium), l (large)")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16,
                        help="Training batch size")
    parser.add_argument("--img_size", type=int, default=640,
                        help="Image size for training and detection")
    parser.add_argument("--model", type=str, default='yolov8n.pt',
                        help="Path to YOLO model file (for detection mode)")
    parser.add_argument("--input", type=str, required=False,
                        help="Path to input image or video file (for detection mode)")
    parser.add_argument("--output", type=str, required=False,
                        help="Path to save output (for detection mode)")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="Confidence threshold (default: 0.25)")
    parser.add_argument("--display", action="store_true",
                        help="Display results while processing")
    
    args = parser.parse_args()
    
    # Mode: Download dataset
    if args.mode in ['download', 'all']:
        dataset_path = download_waste_dataset(args.dataset, args.dataset_dir)
        data_yaml = create_data_yaml(dataset_path)
        print(f"Dataset prepared at {dataset_path}")
        print(f"Data configuration saved to {data_yaml}")
        
        if args.mode == 'download':
            return
    
    # Mode: Train model
    if args.mode in ['train', 'all']:
        if args.mode == 'train':
            # Use existing data.yaml if in train-only mode
            data_yaml = os.path.join(args.dataset_dir, args.dataset, 'waste_containers.yaml')
            if not os.path.exists(data_yaml):
                print(f"Data configuration not found at {data_yaml}")
                print("Creating a new configuration file...")
                data_yaml = create_data_yaml(os.path.join(args.dataset_dir, args.dataset))
        
        # Train the model
        trained_model = train_model(
            data_yaml, 
            model_size=args.model_size,
            epochs=args.epochs,
            img_size=args.img_size,
            batch_size=args.batch_size
        )
        
        print(f"Model training complete. Model saved to {trained_model}")
        
        # Update model path for detection
        args.model = trained_model
    
    # Mode: Detect objects
    if args.mode in ['detect', 'all']:
        # Initialize detector
        detector = WasteDetector(model_path=args.model, conf_threshold=args.conf)
        
        if not args.input and args.mode == 'detect':
            parser.error("--input is required for detection mode")
        
        if args.input:
            # Check if input is image or video
            if args.input.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                # Process image
                try:
                    detected_image, detections = detector.detect(args.input)
                    
                    # Display results
                    if args.display:
                        detected_image.show()
                        
                    # Save output if specified
                    if args.output:
                        detected_image.save(args.output)
                        logger.info(f"Output saved to: {args.output}")
                    
                    # Print detection results
                    print(f"Detected {len(detections)} objects:")
                    waste_bins_detected = 0
                    for obj in detections:
                        if obj.get('is_potential_waste_bin', False):
                            waste_bins_detected += 1
                            print(f"🗑️ {obj['name']} - Confidence: {obj['confidence']}% - "
                                f"Location: ({obj['bbox']['x1']}, {obj['bbox']['y1']}), " 
                                f"({obj['bbox']['x2']}, {obj['bbox']['y2']}) - POTENTIAL WASTE BIN")
                        else:
                            print(f"{obj['name']} - Confidence: {obj['confidence']}% - "
                                f"Location: ({obj['bbox']['x1']}, {obj['bbox']['y1']}), " 
                                f"({obj['bbox']['x2']}, {obj['bbox']['y2']})")
                    
                    print(f"\nTotal waste bins detected: {waste_bins_detected}")
                        
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
                    return 1
                    
            elif args.input.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                # Process video
                try:
                    detector.process_video(
                        args.input, 
                        args.output, 
                        display=args.display
                    )
                except Exception as e:
                    logger.error(f"Error processing video: {e}")
                    return 1
            else:
                logger.error("Unsupported file format. Please use an image or video file.")
                return 1
        else:
            print("No input specified for detection. Skipping detection step.")
    
    return 0

if __name__ == "__main__":
    exit(main())