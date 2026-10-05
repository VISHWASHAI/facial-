import os
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense, BatchNormalization, Input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping, ModelCheckpoint

# Paths to your dataset folders
train_dir = "models/train"
test_dir = "models/test"
MODEL_PATH = "models/emotion_model.h5"


def prep(img):
    """Same preprocessing as utils/emotion_detector.preprocess_face: scale to 0-1."""
    return img.astype("float32") / 255.0


# Augmentation on train only
train_datagen = ImageDataGenerator(
    preprocessing_function=prep,
    rotation_range=15, width_shift_range=0.1, height_shift_range=0.1,
    zoom_range=0.1, horizontal_flip=True,
)
test_datagen = ImageDataGenerator(preprocessing_function=prep)

train_generator = train_datagen.flow_from_directory(
    train_dir, target_size=(48, 48), color_mode="grayscale", batch_size=64, class_mode="categorical")
test_generator = test_datagen.flow_from_directory(
    test_dir, target_size=(48, 48), color_mode="grayscale", batch_size=64,
    class_mode="categorical", shuffle=False)

# "disgust" has ~10x fewer images than the rest, so weight classes
weights = compute_class_weight("balanced", classes=np.unique(train_generator.classes), y=train_generator.classes)
class_weight = dict(enumerate(weights))


def block(filters):
    return [
        Conv2D(filters, (3, 3), padding="same", activation="relu"), BatchNormalization(),
        Conv2D(filters, (3, 3), padding="same", activation="relu"), BatchNormalization(),
        MaxPooling2D(2, 2), Dropout(0.25),
    ]


# Build CNN model (input 48x48x1, softmax over the class folders, same as before)
model = Sequential([Input(shape=(48, 48, 1)), *block(64), *block(128), *block(256),
    Flatten(),
    Dense(256, activation="relu"), BatchNormalization(), Dropout(0.5),
    Dense(train_generator.num_classes, activation="softmax"),
])

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

callbacks = [
    ModelCheckpoint(MODEL_PATH, monitor="val_accuracy", save_best_only=True, verbose=1),
    ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-5, verbose=1),
    EarlyStopping(monitor="val_accuracy", patience=8, restore_best_weights=True),
]

os.makedirs("models", exist_ok=True)
print("Class order:", train_generator.class_indices)
model.fit(train_generator, epochs=50, validation_data=test_generator,
          class_weight=class_weight, callbacks=callbacks)
print(f"✅ Best model saved as {MODEL_PATH}")
