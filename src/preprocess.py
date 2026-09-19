import os
import cv2
import numpy as np

# Dynamically resolve root project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(BASE_DIR, "dataset", "CASIA2")
AU_DIR = os.path.join(DATASET_DIR, "Au")
TP_DIR = os.path.join(DATASET_DIR, "Tp")
MASK_DIR = os.path.join(DATASET_DIR, "Casia 2 Groundtruth")
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "processed")

IMG_SIZE = 224

def get_mask_path(tp_filename):
    """
    Looks up matching mask files in .png format.
    """
    base_name = os.path.splitext(tp_filename)[0]
    base_no_tp = base_name.replace("Tp_", "") if base_name.startswith("Tp_") else base_name

    # Priority lookup for .png masks
    candidates = [
        f"{base_name}.png",
        f"{base_name}_gt.png",
        f"{base_name}_mask.png",
        f"{base_no_tp}.png",
        f"{base_no_tp}_gt.png",
        f"{base_no_tp}_mask.png",
        f"{base_name}.tif",
        f"{base_name}.jpg"
    ]

    for candidate in candidates:
        full_path = os.path.join(MASK_DIR, candidate)
        if os.path.exists(full_path):
            return full_path
    return None

def create_dataset():
    images = []
    class_labels = []
    masks = []

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Process Authentic (Au) Images
    print("Processing Authentic (Au) images...")
    if os.path.exists(AU_DIR):
        for img_name in os.listdir(AU_DIR):
            img_path = os.path.join(AU_DIR, img_name)
            img_array = cv2.imread(img_path)

            if img_array is not None:
                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                resized_img = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))
                images.append(resized_img)  # Store as uint8 (0-255)

                class_labels.append(0)
                blank_mask = np.zeros((IMG_SIZE, IMG_SIZE, 1), dtype=np.uint8)
                masks.append(blank_mask)

    # 2. Process Tampered (Tp) Images and Masks
    print("Processing Tampered (Tp) images and Groundtruth masks...")
    if os.path.exists(TP_DIR):
        for img_name in os.listdir(TP_DIR):
            img_path = os.path.join(TP_DIR, img_name)
            img_array = cv2.imread(img_path)

            if img_array is not None:
                mask_path = get_mask_path(img_name)
                if not mask_path:
                    continue  # Skip unmasked files cleanly

                mask_array = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                if mask_array is None:
                    continue

                img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                resized_img = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))
                images.append(resized_img)  # Store as uint8 (0-255)

                class_labels.append(1)

                # Resize and binarize mask (0 or 255)
                resized_mask = cv2.resize(mask_array, (IMG_SIZE, IMG_SIZE))
                _, binary_mask = cv2.threshold(resized_mask, 127, 255, cv2.THRESH_BINARY)
                masks.append(np.expand_dims(binary_mask, axis=-1))

    # 3. Convert to Compact NumPy Arrays
    print("\nConverting to compact NumPy arrays...")
    X = np.array(images, dtype=np.uint8)
    y_class = np.array(class_labels, dtype=np.uint8)
    y_mask = np.array(masks, dtype=np.uint8)

    print(f"Images shape: {X.shape} (dtype: {X.dtype})")
    print(f"Class labels shape: {y_class.shape} (dtype: {y_class.dtype})")
    print(f"Masks shape: {y_mask.shape} (dtype: {y_mask.dtype})")

    # 4. Save to Disk
    print("\nSaving arrays to disk...")
    np.save(os.path.join(OUTPUT_DIR, 'X.npy'), X)
    np.save(os.path.join(OUTPUT_DIR, 'y_class.npy'), y_class)
    np.save(os.path.join(OUTPUT_DIR, 'y_mask.npy'), y_mask)

    print(f"Preprocessing complete. Files saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    create_dataset()