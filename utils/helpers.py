import os
import sys
import zipfile
import urllib.request
import ctypes
import subprocess
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Constants for downloads
PIPER_ZIP_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
VOICE_ONNX_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
VOICE_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"

# Windows memory query structure
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]

def get_ram_usage():
    """Returns (used_gb, total_gb, percent_load) using Windows GlobalMemoryStatusEx API."""
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total = stat.ullTotalPhys / (1024 ** 3)
        avail = stat.ullAvailPhys / (1024 ** 3)
        used = total - avail
        return round(used, 2), round(total, 2), stat.dwMemoryLoad
    except Exception as e:
        logger.error(f"Error querying RAM: {e}")
        return 0.0, 0.0, 0

def get_cpu_usage():
    """Gets CPU Load Percentage using wmic command line tool."""
    try:
        # Runs wmic to fetch load percentage
        res = subprocess.run(
            ["wmic", "cpu", "get", "LoadPercentage"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = [line.strip() for line in res.stdout.split('\n') if line.strip()]
        if len(lines) > 1:
            return int(lines[1])
    except Exception as e:
        # Fallback to powershell if wmic fails
        try:
            res = subprocess.run(
                ["powershell", "-Command", "(Get-CimInstance Win32_Processor).LoadPercentage"],
                capture_output=True,
                text=True,
                check=True
            )
            return int(res.stdout.strip())
        except:
            pass
    return 0

def check_and_setup_piper(base_dir: Path) -> dict:
    """Checks for piper executable and default model, downloads them if missing."""
    bin_dir = base_dir / "data" / "bin"
    models_dir = base_dir / "data" / "models"
    
    bin_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    piper_exe = bin_dir / "piper" / "piper.exe"
    voice_onnx = models_dir / "en_US-ryan-medium.onnx"
    voice_json = models_dir / "en_US-ryan-medium.onnx.json"
    
    # Setup Piper Binary
    if not piper_exe.exists():
        logger.info("Piper binary not found. Downloading standalone Windows AMD64 package...")
        zip_path = bin_dir / "piper_windows.zip"
        try:
            # Download zip
            urllib.request.urlretrieve(PIPER_ZIP_URL, zip_path)
            logger.info("Piper zip downloaded successfully. Extracting...")
            
            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(bin_dir)
                
            # Remove zip file
            os.remove(zip_path)
            logger.info("Piper setup completed.")
        except Exception as e:
            logger.error(f"Failed to download/extract Piper: {e}")
            return {"status": "error", "message": f"Piper setup failed: {e}"}
            
    # Setup Voice Model
    if not voice_onnx.exists() or not voice_json.exists():
        logger.info("Ryan-Medium voice model not found. Downloading ONNX model files...")
        try:
            if not voice_onnx.exists():
                urllib.request.urlretrieve(VOICE_ONNX_URL, voice_onnx)
            if not voice_json.exists():
                urllib.request.urlretrieve(VOICE_JSON_URL, voice_json)
            logger.info("Voice model downloads completed successfully.")
        except Exception as e:
            logger.error(f"Failed to download voice model: {e}")
            return {"status": "error", "message": f"Voice model download failed: {e}"}
            
    return {
        "status": "ok",
        "piper_exe": str(piper_exe),
        "voice_onnx": str(voice_onnx),
        "voice_json": str(voice_json)
    }
