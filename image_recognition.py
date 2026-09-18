import os
import cv2
from models import ImageAnalysisLog, db
from config import Config

MEDICAL_LABELS = ["Medical document", "X-ray scan", "Dermatology image", "Prescription page"]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS


def _try_classify_with_keras(file_path):
    try:
        from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
        from tensorflow.keras.preprocessing import image as kimage
        import numpy as np

        model = MobileNetV2(weights="imagenet")
        img = kimage.load_img(file_path, target_size=(224, 224))
        x = kimage.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = model.predict(x)
        decoded = decode_predictions(preds, top=5)[0]
        # decoded tuples: (imagenet_id, label, prob)
        results = [(label.replace('_', ' '), float(prob)) for (_, label, prob) in decoded]
        return results
    except Exception:
        return None


def analyze_uploaded_image(user_id, filename, file_path):
    # Try ML-based classification first (optional, requires tensorflow)
    keras_results = _try_classify_with_keras(file_path)
    if keras_results:
        # Attempt to find food-related labels in predictions
        food_like = []
        food_keywords = [
            'pizza', 'hotdog', 'cheeseburger', 'hamburger', 'espresso', 'ice cream', 'ice_cream', 'sushi', 'sandwich',
            'burrito', 'taco', 'spaghetti', 'carbonara', 'salad', 'cupcake', 'bagel', 'pretzel', 'french loaf'
        ]
        for label, prob in keras_results:
            low = label.lower()
            if any(k in low for k in food_keywords) or 'food' in low or 'dish' in low:
                food_like.append((label, prob))

        if food_like:
            label = food_like[0][0]
            confidence = float(food_like[0][1])
            metadata = {"model": "MobileNetV2(ImageNet)", "predictions": keras_results}
            log = ImageAnalysisLog(
                user_id=user_id,
                image_path=filename,
                labels=label,
                confidence=confidence,
                image_metadata=metadata,
            )
            db.session.add(log)
            db.session.commit()
            return {"label": label, "confidence": confidence, "metadata": metadata}

    # Fallback heuristic for non-keras or non-food images
    image = cv2.imread(file_path)
    if image is None:
        raise ValueError("Could not load image for analysis")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_value = gray.mean()
    if mean_value < 70:
        label = "X-ray scan"
        confidence = 0.88
    elif mean_value > 180:
        label = "Medical document"
        confidence = 0.94
    elif mean_value > 120:
        label = "Prescription page"
        confidence = 0.82
    else:
        label = "Dermatology image"
        confidence = 0.78

    metadata = {
        "analysis_type": label,
        "brightness": float(mean_value),
        "dimensions": {"width": int(image.shape[1]), "height": int(image.shape[0])},
    }

    log = ImageAnalysisLog(
        user_id=user_id,
        image_path=filename,
        labels=label,
        confidence=float(confidence),
        image_metadata=metadata,
    )
    db.session.add(log)
    db.session.commit()

    return {"label": label, "confidence": float(confidence), "metadata": metadata}


def ensure_upload_folder():
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
