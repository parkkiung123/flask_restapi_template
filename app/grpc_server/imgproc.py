# webcam_sub.py
import argparse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import os
import cv2
import numpy as np
from app.grpc_server.kotenOCR import ocr
from app.grpc_server.kotenOCR.ndl_parser import convert_to_xml_string3_custom
from app.grpc_server.kotenOCR.reading_order.xy_cut.eval import eval_xml
from app.grpc_server.utils import download_file
import mediapipe as mp  # type:ignore
from mediapipe.tasks import python  # type:ignore
from mediapipe.tasks.python import vision
from keras_facenet import FaceNet

class ImgProcessor:
    def __init__(self):
        self.init_face_detector()
        self.init_face_similarity()
        self.init_kotenOCR_model()

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
    
    def get_koten_orc_result(self, stream):
        try:
            
            tatelinecnt=0
            alllinecnt=0
            npimg = self.pre_process(stream)

            allxmlstr="<OCRDATASET>\n"
            alltextlist=[]
            resjsonarray=[]

            img_h,img_w=npimg.shape[:2]
            detections,classeslist,pil_image=ocr.inference_on_detector_custom(self.detector_ocr,npimage=npimg)
            
            resultobj=[dict(),dict()]
            resultobj[0][0]=list()
            for i in range(16):
                resultobj[1][i]=[]
            for det in detections:
                xmin,ymin,xmax,ymax=det["box"]
                conf=det["confidence"]
                if det["class_index"]==0:
                    resultobj[0][0].append([xmin,ymin,xmax,ymax])
                resultobj[1][det["class_index"]].append([xmin,ymin,xmax,ymax,conf])

            xmlstr=convert_to_xml_string3_custom(img_w, img_h, classeslist, resultobj,score_thr = 0.3,min_bbox_size= 5,use_block_ad= False)
            xmlstr="<OCRDATASET>"+xmlstr+"</OCRDATASET>"
            root = ET.fromstring(xmlstr)
            eval_xml(root, logger=None)
            targetdflist=[]
            with ThreadPoolExecutor(max_workers=8, thread_name_prefix="thread") as executor:
                for lineobj in root.findall(".//LINE"):
                    xmin=int(lineobj.get("X"))
                    ymin=int(lineobj.get("Y"))
                    line_w=int(lineobj.get("WIDTH"))
                    line_h=int(lineobj.get("HEIGHT"))
                    if line_h>line_w:
                        tatelinecnt+=1
                    alllinecnt+=1
                    lineimg=npimg[ymin:ymin+line_h,xmin:xmin+line_w,:]
                    targetdflist.append(lineimg)
                resultlines = executor.map(self.recognizer_ocr.read, targetdflist)
                resultlines=list(resultlines)
                alltextlist.append("\n".join(resultlines))
                for idx,lineobj in enumerate(root.findall(".//LINE")):
                    lineobj.set("STRING",resultlines[idx])
                    xmin=int(lineobj.get("X"))
                    ymin=int(lineobj.get("Y"))
                    line_w=int(lineobj.get("WIDTH"))
                    line_h=int(lineobj.get("HEIGHT"))
                    try:
                        conf=float(lineobj.get("CONF"))
                    except:
                        conf=0
                    jsonobj={"boundingBox": [[xmin,ymin],[xmin,ymin+line_h],[xmin+line_w,ymin],[xmin+line_w,ymin+line_h]],
                        "id": idx,"isVertical": "true","text": resultlines[idx],"isTextline": "true","confidence": conf}
                    resjsonarray.append(jsonobj)
            allxmlstr+=(ET.tostring(root.find("PAGE"), encoding='unicode')+"\n")
            allxmlstr+="</OCRDATASET>"
            if alllinecnt==0 or tatelinecnt/alllinecnt>0.5:
                alltextlist=alltextlist[::-1]
            alljsonobj={
                "contents":[resjsonarray],
                "imginfo": {
                    "img_width": img_w,
                    "img_height": img_h
                }
            }
            npimg = np.array(pil_image)
            return npimg, allxmlstr, alljsonobj, alltextlist
        
        except Exception as e:
            # 必要ならログに出力
            print(f"[ERROR] get_koten_orc_result failed: {e}")
            return None

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
        self.detector_face = vision.FaceDetector.create_from_options(options)
        print("Face Detector initialized.")

    def init_face_similarity(self):
        print("Initializing Face Similarity...")
        self.facenet_model = FaceNet()
        print("Face Similarity initialized.")

    def init_kotenOCR_model(self):
        print("Initializing kotenOCR model...")
        parser = argparse.ArgumentParser(description="Argument for YOLOv9 Inference using ONNXRuntime")
        parser.add_argument("--det-weights", type=str, required=False, help="Path to rtmdet onnx file", default="app/grpc_server/kotenOCR/model/rtmdet-s-1280x1280.onnx")
        parser.add_argument("--det-classes", type=str, required=False, help="Path to list of class in yaml file",default="app/grpc_server/kotenOCR/config/ndl.yaml")
        parser.add_argument("--det-score-threshold", type=float, required=False, default=0.3)
        parser.add_argument("--det-conf-threshold", type=float, required=False, default=0.3)
        parser.add_argument("--det-iou-threshold", type=float, required=False, default=0.3)
        parser.add_argument("--rec-weights", type=str, required=False, help="Path to parseq-tiny onnx file", default="app/grpc_server/kotenOCR/model/parseq-ndl-32x384-tiny-10.onnx")
        parser.add_argument("--rec-classes", type=str, required=False, help="Path to list of class in yaml file", default="app/grpc_server/kotenOCR/config/NDLmoji.yaml")
        parser.add_argument("--device", type=str, required=False, help="Device use (cpu or cude)", choices=["cpu", "cuda"], default="cpu")
        args = parser.parse_args()
        self.recognizer_ocr = ocr.get_recognizer(args=args)
        self.detector_ocr = ocr.get_detector(args=args)
        print("KotenOCR model initialized.")

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
        if self.detector_face is None:
            raise ValueError("Face detector model is not initialized.")
        
        # Mediapipe に渡すため RGBA に変換
        rgb_frame = mp.Image(
            image_format=mp.ImageFormat.SRGBA,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA),
        )

        detection_result = self.detector_face.detect(rgb_frame)
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

