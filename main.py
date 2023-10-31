import cv2
import imutils
from fastapi import FastAPI, Path
from fastapi.responses import StreamingResponse
import asyncio
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

camera_streams = {}


async def video_stream_generator(url_rtsp, capture_flag):
    vs = VideoStream(url_rtsp).start()
    while True:
        frame = vs.read()
        if frame is None:
            print("Frame nih ayi :(:(")
            continue
        frame = imutils.resize(frame, height=480, width=680, )
        output_frame = frame.copy()

        (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
        if flag and capture_flag:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')


@app.get("/stream-video/{device_id}/{user}/{password}/{ip}/{port}/{command}")
async def video_feed(
        device_id: str = Path(..., title="Device ID"),
        user: str = Path(..., title="User"),
        password: str = Path(..., title="Password"),
        ip: str = Path(..., title="IP"),
        port: str = Path(..., title="Port"),
        command: str = Path(..., title="Command")
):
    url_rtsp = f"rtsp://{user}:{password}@{ip}:{port}"

    if command == "capture":
        capture_flag = True
        if device_id not in camera_streams:
            camera_streams[device_id] = video_stream_generator(url_rtsp, capture_flag)
        else:
            camera_streams[device_id] = video_stream_generator(url_rtsp, capture_flag)
            # return "Camera is already streaming."

    elif command == "stop":
        capture_flag = False
        if device_id in camera_streams:
            del camera_streams[device_id]
        else:
            return "Camera is not streaming."

    if device_id not in camera_streams:
        return "Camera is not streaming."

    return StreamingResponse(camera_streams[device_id], media_type="multipart/x-mixed-replace;boundary=frame")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)
