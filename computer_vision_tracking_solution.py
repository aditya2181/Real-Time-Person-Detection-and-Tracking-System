# -*- coding: utf-8 -*-
"""Computer Vision tracking solution.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/16xJhDHaG0Mj_-RAZkD8IfAXyF6WW7BN9
"""

!pip install torch torchvision opencv-python
!pip install yolov5
!pip install deep_sort_realtime
!pip install yt-dlp
!pip install ffmpeg-python

import yt_dlp

# Specifying the path for ffmpeg binary
ydl_opts = {
    'outtmpl': 'yt_video.mp4',  # Specify the output filename and extension
    'ffmpeg_location': r'C:\Users\AdityaSrivastava\ffmpeg\ffmpeg-7.0.2-full_build\ffmpeg-7.0.2-full_build\bin'  # Use a raw string for the path
}

youtube_video_url = 'https://youtu.be/F7_BwCS6r5M?si=ar1qsoGtFdaurSAB'

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([youtube_video_url])

print("Video downloaded successfully with FFmpeg.")

import warnings
import torch
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
from google.colab.patches import cv2_imshow
from IPython.display import display, clear_output

# Suppress specific FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def process_video(video_path, model, tracker):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video stream or file")
        return

    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Original Frame dimensions: {original_width}x{original_height}")

    resize_width, resize_height = 640, 480
    print(f"Resizing frames to: {resize_width}x{resize_height}")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (resize_width, resize_height))

    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video or failed to read frame")
            break

        frame_count += 1
        print(f"Processing frame {frame_count}")

        frame = process_frame(frame, model, tracker, resize_width, resize_height)

        # Display the frame (update every 10 frames to avoid cluttering the output)
        if frame_count % 10 == 0:
            clear_output(wait=True)
            cv2_imshow(frame)
            display(f"Processing frame {frame_count}")

        out.write(frame)

    cap.release()
    out.release()
    print(f"Total frames processed: {frame_count}")
    print("Video processing complete. Output saved as 'output.mp4'")

def process_frame(frame, model, tracker, resize_width, resize_height):
    start_time = time.time()

    frame = cv2.resize(frame, (resize_width, resize_height))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = model(rgb_frame)
    detections = results.xyxy[0].cpu().numpy()

    person_detections = []
    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        if int(cls) == 0:  # Class 0 is for 'person'
            width = x2 - x1
            height = y2 - y1
            person_detections.append([[x1, y1, width, height], conf])

    if len(person_detections) > 0:
        tracks = tracker.update_tracks(person_detections, frame=frame)
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            bbox = track.to_tlbr()
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID: {track_id}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    fps = 1.0 / (time.time() - start_time)
    cv2.putText(frame, f'FPS: {fps:.2f}', (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    return frame

def live_webcam_test(model, tracker):
    cap = cv2.VideoCapture(0)  # 0 is the ID for the primary webcam
    if not cap.isOpened():
        print("Error opening webcam")
        return

    resize_width, resize_height = 640, 480
    print(f"Resizing webcam frames to: {resize_width}x{resize_height}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        frame = process_frame(frame, model, tracker, resize_width, resize_height)

        # Display the frame
        cv2.imshow('Live Webcam Test', frame)

        # Break the loop if the user presses 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Webcam test finished")

def main():
    print("Loading YOLOv5 model...")
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)

    tracker = DeepSort(max_age=30, n_init=2, nms_max_overlap=1.0, max_iou_distance=0.7)

    video_path = '/content/yt_video.mp4'
    print(f"Processing video: {video_path}")
    process_video(video_path, model, tracker)

    print("Starting live webcam testing...")
    live_webcam_test(model, tracker)

if __name__ == "__main__":
    main()