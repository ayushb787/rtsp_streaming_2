import cv2
import imutils
from fastapi import FastAPI, Path
from fastapi.responses import StreamingResponse
from imutils.video import VideoStream
from starlette.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Camera:
    def __init__(self, device_id, user, password, ip, port,channel, subtype):
        self.device_id = device_id
        self.user = user
        self.password = password
        self.ip = ip
        self.port = port
        self.channel = channel
        self.subtype = subtype
        self.capture_flag = False
        self.vs = None

    def start_streaming(self):
        self.capture_flag = True
        # Reinitialize VideoStream to start from real-time
        rtsp = f"rtsp://{self.user}:{self.password}@{self.ip}:{self.port}/cam/realmonitor?channel={self.channel}&subtype={self.subtype}"
        print(rtsp)
        self.vs = VideoStream(rtsp).start()
        while self.vs is None:
            pass
        

    def stop_streaming(self):
        self.capture_flag = False
        if self.vs:
            self.vs.stop()
            self.vs = None

    def generate_video_frames(self):
        while self.capture_flag:
            frame = self.vs.read()
            if frame is None:
                continue
            frame = imutils.resize(frame, height=480, width=680)
            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if flag:
                yield (
                        b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                        bytearray(encodedImage) + b'\r\n'
                )


camera_instances = {}


@app.get("/stream-video/{device_id}/{user}/{password}/{ip}/{port}/{channel}/{subtype}/{command}")
async def video_feed(
        device_id: str = Path(..., title="Device ID"),
        user: str = Path(..., title="User"),
        password: str = Path(..., title="Password"),
        ip: str = Path(..., title="IP"),
        port: str = Path(..., title="Port"),
        channel: str =Path(...,title="Channel"),
        subtype: str =Path(...,title="Subtype"),
        command: str = Path(..., title="Command")
):
    if command == "capture":
        if device_id not in camera_instances or not camera_instances[device_id].capture_flag:
            camera = Camera(device_id, user, password, ip, port, channel, subtype)
            camera_instances[device_id] = camera
            camera.start_streaming()
        else:
            camera = camera_instances[device_id]
            # Stop the previous stream
            camera.stop_streaming()
            # Start a new stream from real-time
            camera.start_streaming()

    elif command == "stop":
        if device_id in camera_instances:
            camera = camera_instances[device_id]
            camera.stop_streaming()
            del camera_instances[device_id]
        else:
            return "Camera is not streaming."

    if device_id not in camera_instances:
        return "Camera is not streaming."

    return StreamingResponse(camera_instances[device_id].generate_video_frames(),
                             media_type="multipart/x-mixed-replace;boundary=frame")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=6065)
