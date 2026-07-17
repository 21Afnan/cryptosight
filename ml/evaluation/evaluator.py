import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, log_loss, mean_squared_error, mean_absolute_error, r2_score

def evaluate_classification(model, X_train, y_train, X_val, y_val, X_test, y_test):
    """
    Evaluates a classification model on train, validation, and test datasets.
    Returns a dictionary of metrics and the prediction arrays.
    """
    # Predictions
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    test_preds = model.predict(X_test)

    # Probabilities
    try:
        train_proba = model.predict_proba(X_train)
        val_proba = model.predict_proba(X_val)
        test_proba = model.predict_proba(X_test)
        train_loss = float(log_loss(y_train, train_proba))
        val_loss = float(log_loss(y_val, val_proba))
        test_loss = float(log_loss(y_test, test_proba))
    except Exception:
        train_loss, val_loss, test_loss = 0.0, 0.0, 0.0
        val_proba = None

    # Accuracies
    train_acc = float(accuracy_score(y_train, train_preds))
    val_acc = float(accuracy_score(y_val, val_preds))
    test_acc = float(accuracy_score(y_test, test_preds))

    # Precision / Recall (Validation)
    val_prec = float(precision_score(y_val, val_preds, average="weighted", zero_division=0))
    val_rec = float(recall_score(y_val, val_preds, average="weighted", zero_division=0))

    # Raw Correct Counts
    correct_train_count = int(np.sum(train_preds == y_train))
    correct_val_count = int(np.sum(val_preds == y_val))
    correct_test_count = int(np.sum(test_preds == y_test))

    # Compile metrics
    metrics = {
        "train_loss": train_loss,
        "val_loss": val_loss,
        "test_loss": test_loss,
        "train_acc": train_acc,
        "val_acc": val_acc,
        "test_acc": test_acc,
        "val_prec": val_prec,
        "val_rec": val_rec,
        "correct_train_count": correct_train_count,
        "total_train": len(y_train),
        "correct_val_count": correct_val_count,
        "total_val": len(y_val),
        "correct_test_count": correct_test_count,
        "total_test": len(y_test)
    }

    # Compile raw predictions for further use
    predictions = {
        "train_preds": train_preds,
        "val_preds": val_preds,
        "test_preds": test_preds,
        "val_proba": val_proba
    }

    return metrics, predictions


def evaluate_regression(model, X_train, y_train, X_val, y_val, X_test, y_test):
    """
    Evaluates a sklearn-compatible regression model on train, validation, and test datasets.
    Returns a dictionary of formatted metrics and continuous prediction arrays.
    NOTE: For lstm_regressor (PyTorch), metrics are computed inside pytorch_lstm.py directly.
    """
    train_preds = model.predict(X_train)
    val_preds   = model.predict(X_val)
    test_preds  = model.predict(X_test)

    metrics = {
        "train_rmse":  round(float(np.sqrt(mean_squared_error(y_train, train_preds))), 6),
        "val_rmse":    round(float(np.sqrt(mean_squared_error(y_val,   val_preds))),   6),
        "test_rmse":   round(float(np.sqrt(mean_squared_error(y_test,  test_preds))),  6),
        "train_mae":   round(float(mean_absolute_error(y_train, train_preds)), 6),
        "val_mae":     round(float(mean_absolute_error(y_val,   val_preds)),   6),
        "test_mae":    round(float(mean_absolute_error(y_test,  test_preds)),  6),
        "train_r2":    round(float(r2_score(y_train, train_preds)), 4),
        "val_r2":      round(float(r2_score(y_val,   val_preds)),   4),
        "test_r2":     round(float(r2_score(y_test,  test_preds)),  4),
        "total_train": int(len(y_train)),
        "total_val":   int(len(y_val)),
        "total_test":  int(len(y_test))
    }

    predictions = {
        "train_preds": train_preds,
        "val_preds":   val_preds,
        "test_preds":  test_preds
    }

    return metrics, predictions


def create_leaderboard_entry(task: str, model_name: str, metrics: dict, model_save_path: str, pred_save_path: str, hyperparameters: dict = None, trading_metrics: dict = None) -> dict:
    """
    Creates a standardized leaderboard dictionary entry for any model type.
    """
    entry = {
        "model": model_name,
        "hyperparameters": hyperparameters or {},
        "trading_metrics": trading_metrics or {},
        "model_file": str(model_save_path),
        "prediction_file": str(pred_save_path)
    }

    if task == "classification":
        entry.update({
            "train_accuracy": f"{metrics.get('train_acc', 0) * 100.0:.2f}%",
            "train_correct": metrics.get('correct_train_count', 0),
            "train_total": metrics.get('total_train', 0),
            "train_loss": round(metrics.get('train_loss', 0), 4),
            
            "val_accuracy": f"{metrics.get('val_acc', 0) * 100.0:.2f}%",
            "val_precision": f"{metrics.get('val_prec', 0) * 100.0:.2f}%",
            "val_recall": f"{metrics.get('val_rec', 0) * 100.0:.2f}%",
            "val_correct": metrics.get('correct_val_count', 0),
            "val_total": metrics.get('total_val', 0),
            "val_loss": round(metrics.get('val_loss', 0), 4),
            
            "test_accuracy": f"{metrics.get('test_acc', 0) * 100.0:.2f}%",
            "test_correct": metrics.get('correct_test_count', 0),
            "test_total": metrics.get('total_test', 0),
            "test_loss": round(metrics.get('test_loss', 0), 4),
        })
    elif task == "regression":
        entry.update({
            "train_rmse":  metrics.get("train_rmse"),
            "train_mae":   metrics.get("train_mae"),
            "train_r2":    metrics.get("train_r2"),
            "train_total": metrics.get("total_train"),
            "val_rmse":    metrics.get("val_rmse"),
            "val_mae":     metrics.get("val_mae"),
            "val_r2":      metrics.get("val_r2"),
            "val_total":   metrics.get("total_val"),
            "test_rmse":   metrics.get("test_rmse"),
            "test_mae":    metrics.get("test_mae"),
            "test_r2":     metrics.get("test_r2"),
            "test_total":  metrics.get("total_test"),
        })

    return entry
