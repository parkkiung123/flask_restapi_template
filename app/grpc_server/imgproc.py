# webcam_sub.py
import os
import cv2
import numpy as np
from app.grpc_server.utils import download_file
import mediapipe as mp  # type:ignore
from mediapipe.tasks import python  # type:ignore
from mediapipe.tasks.python import vision
from keras_facenet import FaceNet

class ImgProcessor:
    def __init__(self):
        self.init_face_detector()
        self.init_face_similarity()

    def get_grayscale(self, stream):
        return self.process(stream, grayscale=True)

    def get_face_crop(self, stream):
        return self.process(stream, face_crop=True)
    
    def get_face_similarity(self, stream1, stream2):
        if self.facenet_model is None:
            raise ValueError("Face similarity model is not initialized.")

        frame1 = self.pre_process(stream1)
        frame2 = self.pre_process(stream2)

        # 顔の検出
        face1 = self.face_crop(frame1)
        face2 = self.face_crop(frame2)

        if face1 is None or face2 is None:
            return None

        # 顔の類似度計算
        face1_embedding = self.facenet_model.embeddings(np.expand_dims(face1, axis=0))
        face2_embedding = self.facenet_model.embeddings(np.expand_dims(face2, axis=0))

        # コサイン類似度を計算
        similarity = np.dot(face1_embedding, face2_embedding.T) / (
            np.linalg.norm(face1_embedding) * np.linalg.norm(face2_embedding)
        )

        return similarity[0][0]

    def init_face_detector(self):
        print("Initializing Face Detector...")
        model_url = 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite'
        # ダウンロードファイル名生成
        model_name = model_url.split('/')[-1]
        quantize_type = model_url.split('/')[-3]
        split_name = model_name.split('.')
        model_name = split_name[0] + '_' + quantize_type + '.' + split_name[1]
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(BASE_DIR, 'model', model_name)
        # 重みファイルダウンロード
        if not os.path.exists(model_path):
            download_file(url=model_url, save_path=model_path)
        # Face Detector生成
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(base_options=base_options, )
        self.detector = vision.FaceDetector.create_from_options(options)
        print("Face Detector initialized.")

    def init_face_similarity(self):
        print("Initializing Face Similarity...")
        self.facenet_model = FaceNet()
        print("Face Similarity initialized.")

    def pre_process(self, stream):
        # バイナリからNumPy配列に変換
        file_bytes = stream.read()
        np_arr = np.frombuffer(file_bytes, np.uint8)
        # OpenCVで画像として読み込む
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return frame

    def process(self, stream, grayscale=False, face_crop=False):
        frame = self.pre_process(stream).copy()

        if grayscale:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        if face_crop:
            frame = self.face_crop(frame)
        
        frame = self.post_process(frame)

        return frame 
    
    def post_process(self, frame):
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
    
    def face_crop(self, frame):
        if self.detector is None:
            raise ValueError("Face detector model is not initialized.")
        
        # Mediapipe に渡すため RGBA に変換
        rgb_frame = mp.Image(
            image_format=mp.ImageFormat.SRGBA,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA),
        )

        detection_result = self.detector.detect(rgb_frame)
        image_height, image_width = frame.shape[:2]

        # 顔が検出されなければ None を返す
        if not detection_result.detections:
            return None

        # 最初の顔のみ crop する
        detection_info = detection_result.detections[0]

        x1 = detection_info.bounding_box.origin_x
        y1 = detection_info.bounding_box.origin_y
        x2 = x1 + detection_info.bounding_box.width
        y2 = y1 + detection_info.bounding_box.height

        # 範囲を画像内にクリップ
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(image_width, x2)
        y2 = min(image_height, y2)

        # 顔領域を crop
        cropped_face = frame[y1:y2, x1:x2]

        return cropped_face

