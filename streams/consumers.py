import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
import ffmpeg
from urllib.parse import parse_qs
import time

logger = logging.getLogger(__name__)

class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        query_params = parse_qs(self.scope["query_string"].decode())
        rtsp_url = query_params.get("rtsp", [None])[0]
        stream_url = rtsp_url
        logger.info(f"WebSocket connect: stream_id={self.stream_id}")

        await self.accept()

        max_retries = 1
        retry_delay = 3

        for attempt in range(max_retries):
            process = None
            try:
                logger.info(f"Starting FFmpeg (Attempt {attempt + 1}/{max_retries})")
                logger.info(f"Starting FFmpeg for RTSP: {stream_url}")      
                process = (
                ffmpeg
                .input(stream_url, rtsp_flags='prefer_tcp', timeout=10000000)
                .output(
                    'pipe:',
                    format='mpegts',
                    vcodec='h264',
                    acodec='aac',
                    loglevel='error',
                    fflags='+genpts'
                )
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

                logger.info("FFmpeg process started")

                async def log_ffmpeg_stderr():
                    try:
                        while not process.stderr.closed:
                            line = await asyncio.get_event_loop().run_in_executor(None, process.stderr.readline)
                            if not line:
                                break
                            logger.warning(f"FFmpeg stderr: {line.decode().strip()}")
                    except Exception as e:
                        logger.error(f"FFmpeg stderr logging error: {str(e)}")

                asyncio.create_task(log_ffmpeg_stderr())

                try:
                    while True:
                        chunk = await asyncio.get_event_loop().run_in_executor(None, lambda: process.stdout.read(1024 * 128))
                        if not chunk:
                            logger.info("No more FFmpeg stdout data")
                            break
                        logger.info(f"Sending chunk at {time.time()}")
                        await self.send(bytes_data=chunk)
                except Exception as e:
                    logger.error(f"Error reading FFmpeg stdout: {str(e)}")
                    await self.send(text_data=f"Error reading FFmpeg stdout: {str(e)}")

                process.stdout.close()
                if process.stderr:
                    process.stderr.close()
                return_code = await asyncio.get_event_loop().run_in_executor(None, process.wait)
                if return_code == 0:
                    logger.info("FFmpeg exited successfully")
                    break
                logger.error(f"FFmpeg exited with code {return_code}")
                await self.send(text_data=f"FFmpeg failed with code {return_code}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying FFmpeg in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

            except ffmpeg.Error as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                logger.error(f"FFmpeg error: {error_msg}")
                await self.send(text_data=f"FFmpeg error: {error_msg}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying FFmpeg in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                await self.send(text_data=f"Unexpected error: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying FFmpeg in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
            finally:
                if process:
                    try:
                        process.terminate()
                        await asyncio.get_event_loop().run_in_executor(None, lambda: process.wait(timeout=2))
                    except Exception as e:
                        logger.error(f"Error terminating FFmpeg process: {str(e)}")

        await self.close()

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: stream_id={self.stream_id}, code={close_code}")