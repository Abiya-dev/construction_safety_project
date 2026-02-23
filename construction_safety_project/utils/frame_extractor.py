import cv2

def get_video_capture(video_path):
    return cv2.VideoCapture(video_path)
