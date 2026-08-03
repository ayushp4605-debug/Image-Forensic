import numpy as np
from PIL import Image
import io

def compute_ela(image: Image.Image, quality: int = 90, scale: int = 15) -> np.ndarray:
    """
    Computes Error Level Analysis (ELA) map for a given PIL Image object.
    
    Parameters:
        image (PIL.Image): Input image.
        quality (int): JPEG quality level for re-compression (1-100).
        scale (int): Multiplier to amplify the residual error for visualization.
        
    Returns:
        np.ndarray: Scaled ELA heatmap array (RGB, uint8).
    """
    # 1. Convert input image to RGB
    orig_img = image.convert('RGB')
    
    # 2. Re-compress image in memory to JPEG at specified quality
    buffer = io.BytesIO()
    orig_img.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)
    
    # 3. Read compressed image back
    compressed_img = Image.open(buffer)
    
    # 4. Convert both to float32 NumPy arrays for subtraction
    orig_np = np.array(orig_img, dtype=np.float32)
    comp_np = np.array(compressed_img, dtype=np.float32)
    
    # 5. Compute absolute pixel-wise difference
    diff = np.abs(orig_np - comp_np)
    
    # 6. Amplify the error by the scale factor
    ela_map = diff * scale
    
    # 7. Clip values to valid image range [0, 255] and convert back to uint8
    ela_map = np.clip(ela_map, 0, 255).astype(np.uint8)
    
    return ela_map