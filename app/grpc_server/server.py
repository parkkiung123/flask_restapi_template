import io
import cv2
import grpc
from concurrent import futures
from app.grpc_server import image_pb2, image_pb2_grpc
from app.grpc_server.imgproc import ImgProcessor  # 既存ロジックを流用

processor = ImgProcessor()

def handle_request_image(image_bytes, fn):
    return fn(io.BytesIO(image_bytes))  # get_gray などは stream が引数

class ImageProcessorServicer(image_pb2_grpc.ImageProcessorServicer):
    def GetGray(self, request, context):
        result = handle_request_image(request.image, processor.get_grayscale)
        _, buf = cv2.imencode('.jpg', result)
        return image_pb2.ImageResponse(image=buf.tobytes())

    def GetCropFace(self, request, context):
        result = handle_request_image(request.image, processor.get_face_crop)
        if result is None:
            return image_pb2.ImageResponse()
        _, buf = cv2.imencode('.jpg', result)
        return image_pb2.ImageResponse(image=buf.tobytes())

    def GetFaceSimilarity(self, request, context):
        sim = processor.get_face_similarity(
            io.BytesIO(request.image1),
            io.BytesIO(request.image2)
        )
        if sim is None:
            return image_pb2.FaceSimilarityResponse(similarity=0.0)
        return image_pb2.FaceSimilarityResponse(similarity=sim)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    image_pb2_grpc.add_ImageProcessorServicer_to_server(ImageProcessorServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
