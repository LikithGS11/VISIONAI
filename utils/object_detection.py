from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image
import os
import time
import argparse
from typing import List, Dict, Tuple, Optional, Union
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("yolo_detector")

class YOLODetector:
    """A class for object detection using YOLOv8 models."""
    
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.25):
        """
        Initialize the YOLO detector.
        
        Args:
            model_path: Path to the YOLO model file
            conf_threshold: Confidence threshold for detections
        """
        self.conf_threshold = conf_threshold
        try:
            start_time = time.time()
            self.model = YOLO(model_path)
            logger.info(f"Model loaded in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def detect(self, 
               image: Union[str, np.ndarray, Image.Image], 
               visualize: bool = True
              ) -> Tuple[Optional[Image.Image], List[Dict]]:
        """
        Detect objects in an image.
        
        Args:
            image: Input image (file path, numpy array, or PIL Image)
            visualize: Whether to draw bounding boxes on the image
            
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
                    }
                }
                detected_objects.append(detection_info)
                
                # Draw bounding box if visualization is enabled
                if visualize:
                    # Generate a unique color for this class
                    color = self._get_color_for_class(cls)
                    
                    # Draw bounding box
                    cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw filled background for text
                    text = f"{class_name} {conf:.2f}"
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
        Process a video file for object detection.
        
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
                    cv2.imshow('YOLO Detection', opencv_frame)
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

def main():
    """Main function to run the detector from command line."""
    parser = argparse.ArgumentParser(description="YOLO Object Detection")
    parser.add_argument("--input", "-i", type=str, required=True, 
                        help="Path to input image or video file")
    parser.add_argument("--output", "-o", type=str, 
                        help="Path to save output (optional)")
    parser.add_argument("--model", "-m", type=str, default="yolov8n.pt",
                        help="Path to YOLO model file (default: yolov8n.pt)")
    parser.add_argument("--conf", "-c", type=float, default=0.25,
                        help="Confidence threshold (default: 0.25)")
    parser.add_argument("--display", "-d", action="store_true",
                        help="Display results while processing")
    parser.add_argument("--skip", "-s", type=int, default=0,
                        help="Skip frames for faster video processing (default: 0)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Initialize detector
    detector = YOLODetector(model_path=args.model, conf_threshold=args.conf)
    
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
            logger.info(f"Detected {len(detections)} objects:")
            for obj in detections:
                logger.info(f"{obj['name']} - Confidence: {obj['confidence']}% - "
                          f"Location: ({obj['bbox']['x1']}, {obj['bbox']['y1']}), " 
                          f"({obj['bbox']['x2']}, {obj['bbox']['y2']})")
                
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return 1
            
    elif args.input.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        # Process video
        try:
            detector.process_video(
                args.input, 
                args.output, 
                display=args.display,
                skip_frames=args.skip
            )
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return 1
    else:
        logger.error("Unsupported file format. Please use an image or video file.")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())