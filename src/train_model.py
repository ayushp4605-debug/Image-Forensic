import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, optimizers
from sklearn.model_selection import train_test_split

# ==========================================
# 0. CONFIGURATION & GPU SETUP
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "dataset", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "src", "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)

IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 20

# ==========================================
# 1. DATA LOADING & 70/30 STRATIFIED SPLIT
# ==========================================
print("Loading preprocessed dataset arrays...")
X = np.load(os.path.join(PROCESSED_DIR, "X.npy"), mmap_mode='r') # mmap to save active RAM
y_class = np.load(os.path.join(PROCESSED_DIR, "y_class.npy"))
y_mask = np.load(os.path.join(PROCESSED_DIR, "y_mask.npy"), mmap_mode='r')

indices = np.arange(len(y_class))
train_idx, test_idx = train_test_split(
    indices, 
    test_size=0.30, 
    random_state=42, 
    stratify=y_class
)

print(f"Total dataset size : {len(y_class)}")
print(f"Training set (70%) : {len(train_idx)} samples")
print(f"Testing set  (30%) : {len(test_idx)} samples")

# Generator to stream uint8 data and normalize to float32 on-the-fly
def data_generator(indices_list, batch_size, target_type='both'):
    num_samples = len(indices_list)
    while True:
        np.random.shuffle(indices_list)
        for offset in range(0, num_samples, batch_size):
            batch_indices = indices_list[offset:offset + batch_size]
            
            # On-the-fly normalization from [0, 255] uint8 to [0.0, 1.0] float32
            batch_x = np.array(X[batch_indices], dtype=np.float32) / 255.0
            
            if target_type == 'class':
                batch_y = np.array(y_class[batch_indices], dtype=np.float32)
                yield batch_x, batch_y
            elif target_type == 'mask':
                batch_m = np.array(y_mask[batch_indices], dtype=np.float32) / 255.0
                yield batch_x, batch_m
            else:
                batch_y = np.array(y_class[batch_indices], dtype=np.float32)
                batch_m = np.array(y_mask[batch_indices], dtype=np.float32) / 255.0
                yield batch_x, {"classifier_output": batch_y, "localizer_output": batch_m}

train_steps = int(np.ceil(len(train_idx) / BATCH_SIZE))
val_steps = int(np.ceil(len(test_idx) / BATCH_SIZE))

# ==========================================
# 2. MODEL 1: EFFICIENTNET-B4 CLASSIFIER
# ==========================================
def build_classifier():
    # Base pre-trained model
    base_model = tf.keras.applications.EfficientNetB4(
        include_top=False, 
        weights='imagenet', 
        input_shape=(IMG_SIZE, IMG_SIZE, 3)
    )
    base_model.trainable = True
    
    # Freeze the initial layers, fine-tune the top 30 layers
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = base_model(inputs)
    x = layers.GlobalAveragePooling2D()(x)

    # -------------------------------------------------------------------------
    # BATCH NORMALIZATION & HE INITIALIZATION EXPLANATION:
    # 1. kernel_initializer='he_normal': Sets initial weights proportional to 
    #    sqrt(2 / fan_in) to preserve signal variance across deep layers.
    # 2. BatchNormalization(): Computes mini-batch mean and variance, zero-centers
    #    activations, and scales with learnable gamma/beta parameters.
    #    This removes reliance on precise weight scales and accelerates training.
    # -------------------------------------------------------------------------
    x = layers.Dense(256, kernel_initializer='he_normal', use_bias=False)(x)
    x = layers.BatchNormalization()(x) # Re-normalizes feature distributions
    x = layers.Activation('relu')(x)
    x = layers.Dropout(0.4)(x)

    x = layers.Dense(64, kernel_initializer='he_normal', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.Dropout(0.2)(x)

    outputs = layers.Dense(1, activation='sigmoid')(x)
    
    model = models.Model(inputs, outputs, name="RavenLens_Classifier")
    return model

# ==========================================
# 3. MODEL 2: U-NET LOCALIZATION NETWORK
# ==========================================
def conv_block(input_tensor, num_filters):
    """
    Standard double convolution block with He Normal Initialization and Batch Normalization.
    """
    # First Conv -> BN -> ReLU
    x = layers.Conv2D(num_filters, (3, 3), padding="same", 
                      kernel_initializer='he_normal', use_bias=False)(input_tensor)
    x = layers.BatchNormalization()(x) # Stabilizes training dynamics
    x = layers.Activation("relu")(x)

    # Second Conv -> BN -> ReLU
    x = layers.Conv2D(num_filters, (3, 3), padding="same", 
                      kernel_initializer='he_normal', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    return x

def build_unet():
    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))

    # Encoder (Downsampling)
    c1 = conv_block(inputs, 32)
    p1 = layers.MaxPooling2D((2, 2))(c1)

    c2 = conv_block(p1, 64)
    p2 = layers.MaxPooling2D((2, 2))(c2)

    c3 = conv_block(p2, 128)
    p3 = layers.MaxPooling2D((2, 2))(c3)

    # Bottleneck
    b = conv_block(p3, 256)

    # Decoder (Upsampling with Skip Connections)
    u1 = layers.Conv2DTranspose(128, (2, 2), strides=(2, 2), padding="same")(b)
    u1 = layers.concatenate([u1, c3])
    c4 = conv_block(u1, 128)

    u2 = layers.Conv2DTranspose(64, (2, 2), strides=(2, 2), padding="same")(c4)
    u2 = layers.concatenate([u2, c2])
    c5 = conv_block(u2, 64)

    u3 = layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding="same")(c5)
    u3 = layers.concatenate([u3, c1])
    c6 = conv_block(u3, 32)

    outputs = layers.Conv2D(1, (1, 1), activation="sigmoid")(c6)

    model = models.Model(inputs, outputs, name="RavenLens_UNet")
    return model

# Combined Dice + Binary Cross-Entropy Loss for U-Net
def dice_bce_loss(y_true, y_pred):
    bce = tf.keras.losses.binary_crossentropy(y_true, y_pred)
    smooth = 1e-6
    y_true_f = tf.reshape(y_true, [-1])
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    dice = (2. * intersection + smooth) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + smooth)
    return bce + (1.0 - dice)

# ==========================================
# 4. TRAINING EXECUTION
# ==========================================
if __name__ == "__main__":
    # --- A. TRAIN CLASSIFIER ---
    print("\n" + "="*50)
    print("STAGE 1: TRAINING EFFICIENTNET-B4 CLASSIFIER")
    print("="*50)
    
    classifier = build_classifier()
    classifier.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
    )

    classifier_callbacks = [
        callbacks.ModelCheckpoint(
            os.path.join(MODELS_DIR, "best_classifier.keras"), 
            save_best_only=True, 
            monitor="val_loss", 
            mode="min"
        ),
        callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6)
    ]

    classifier.fit(
        data_generator(train_idx.copy(), BATCH_SIZE, target_type='class'),
        steps_per_epoch=train_steps,
        validation_data=data_generator(test_idx.copy(), BATCH_SIZE, target_type='class'),
        validation_steps=val_steps,
        epochs=EPOCHS,
        callbacks=classifier_callbacks
    )

    # --- B. TRAIN U-NET LOCALIZER ---
    print("\n" + "="*50)
    print("STAGE 2: TRAINING U-NET LOCALIZER")
    print("="*50)
    
    unet = build_unet()
    unet.compile(
        optimizer=optimizers.Adam(learning_rate=1e-4),
        loss=dice_bce_loss,
        metrics=['binary_accuracy']
    )

    unet_callbacks = [
        callbacks.ModelCheckpoint(
            os.path.join(MODELS_DIR, "best_unet.keras"), 
            save_best_only=True, 
            monitor="val_loss", 
            mode="min"
        ),
        callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6)
    ]

    unet.fit(
        data_generator(train_idx.copy(), BATCH_SIZE, target_type='mask'),
        steps_per_epoch=train_steps,
        validation_data=data_generator(test_idx.copy(), BATCH_SIZE, target_type='mask'),
        validation_steps=val_steps,
        epochs=EPOCHS,
        callbacks=unet_callbacks
    )

    print("\nTraining completed successfully! Saved models are in src/saved_models/")