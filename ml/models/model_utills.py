import joblib
import numpy as np
from sklearn.utils.class_weight import compute_sample_weight

def train_model(model_name: str, model, X_train, y_train, task: str = "classification", **kwargs):
    """
    Trains the model. Automatically handles custom logic like XGBoost sample weighting.
    """
    # Apply balanced sample weights for XGBoost classification
    if task == "classification" and model_name == "xgboost":
        sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)
        model.fit(X_train, y_train, sample_weight=sample_weights, **kwargs)
    else:
        model.fit(X_train, y_train, **kwargs)
        
    return model

def save_model(model, filepath: str):
    """Saves the trained model."""
    joblib.dump(model, filepath)

def load_model(filepath: str):
    """Loads a trained model from disk."""
    return joblib.load(filepath)
