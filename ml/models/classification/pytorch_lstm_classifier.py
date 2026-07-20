from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import accuracy_score, precision_score, recall_score, log_loss

from cryptosight.utils.logger import get_logger
from cryptosight.ml.models.regression.pytorch_lstm import build_sequences

logger = get_logger("PyTorchLSTMClassifier")


class LSTMClassifierNet(nn.Module):
    """
    LSTM Neural Network for quantitative trading directional classification.
    Input shape: (batch, seq_len, features)
    Output shape: (batch, num_classes) — logits for each class
    """

    def __init__(self, input_size, hidden_size, num_layers, num_classes=3, dropout=0.0):
        super(LSTMClassifierNet, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        # Take only the last timestep's output
        logits = self.fc(lstm_out[:, -1, :])
        return logits


def train_pytorch_lstm_classifier(X_train, y_train_mapped, X_val, y_val_mapped, X_test, y_test_mapped, params, save_path):
    """
    Train a PyTorch LSTM classifier with proper time-series sequences.
    Called directly from ClassifierPipeline when model_name == 'lstm_classifier'.

    Sliding window of `lookback_window` past bars is built per split before training.

    Returns:
        metrics        - dict of accuracy/loss/precision/recall for train/val/test
        predictions    - dict of train_preds / val_preds / test_preds / val_proba
        trained_params - hyperparams dict for JSON
        model          - the trained LSTMClassifierNet instance
    """
    hidden_size     = int(params.get("hidden_size"))
    num_layers      = int(params.get("num_layers"))
    epochs          = int(params.get("epochs"))
    batch_size      = int(params.get("batch_size"))
    learning_rate   = float(params.get("learning_rate"))
    dropout         = float(params.get("dropout"))
    lookback        = int(params.get("lookback_window"))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(
        f"Training LSTM Classifier | Device: {device} | "
        f"Hidden: {hidden_size} | Layers: {num_layers} | "
        f"Lookback: {lookback} | Epochs: {epochs}"
    )

    # Convert pandas DataFrames to numpy arrays if necessary to avoid indexing warnings
    X_train_np = X_train.values if isinstance(X_train, pd.DataFrame) else X_train
    X_val_np   = X_val.values   if isinstance(X_val, pd.DataFrame) else X_val
    X_test_np  = X_test.values  if isinstance(X_test, pd.DataFrame) else X_test

    # ── Build sliding window sequences ───────────────────────────────────────
    # Each sample is now a real temporal sequence of `lookback` past candles
    X_train_seq, y_train_seq = build_sequences(X_train_np, y_train_mapped, lookback)
    X_val_seq,   y_val_seq   = build_sequences(X_val_np,   y_val_mapped,   lookback)
    X_test_seq,  y_test_seq  = build_sequences(X_test_np,  y_test_mapped,  lookback)

    # Ensure target values are integers
    y_train_seq = y_train_seq.astype(np.int64)
    y_val_seq   = y_val_seq.astype(np.int64)
    y_test_seq  = y_test_seq.astype(np.int64)

    logger.info(
        f"Sequence shapes | Train: {X_train_seq.shape} | "
        f"Val: {X_val_seq.shape} | Test: {X_test_seq.shape}"
    )

    input_size = X_train_seq.shape[2]   # number of features
    model = LSTMClassifierNet(input_size, hidden_size, num_layers, num_classes=3, dropout=dropout).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn   = nn.CrossEntropyLoss()

    # ── Training loop ─────────────────────────────────────────────────────────
    dataset = TensorDataset(
        torch.tensor(X_train_seq, dtype=torch.float32),
        torch.tensor(y_train_seq, dtype=torch.long)
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_X)
            loss   = loss_fn(logits, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(f"  Epoch [{epoch+1}/{epochs}] Loss: {epoch_loss / len(loader):.6f}")

    # ── Predict on all splits ─────────────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        def get_preds_and_proba(X_seq):
            tensor_X = torch.tensor(X_seq, dtype=torch.float32).to(device)
            logits = model(tensor_X)
            proba = torch.softmax(logits, dim=1).cpu().numpy()
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            return preds, proba

        train_preds, train_proba = get_preds_and_proba(X_train_seq)
        val_preds, val_proba     = get_preds_and_proba(X_val_seq)
        test_preds, test_proba   = get_preds_and_proba(X_test_seq)

    # ── Metrics (computed on sequenced targets) ───────────────────────────────
    metrics = {
        "train_loss": float(log_loss(y_train_seq, train_proba)),
        "val_loss":   float(log_loss(y_val_seq, val_proba)),
        "test_loss":  float(log_loss(y_test_seq, test_proba)),
        "train_acc":  float(accuracy_score(y_train_seq, train_preds)),
        "val_acc":    float(accuracy_score(y_val_seq, val_preds)),
        "test_acc":   float(accuracy_score(y_test_seq, test_preds)),
        "val_prec":   float(precision_score(y_val_seq, val_preds, average="weighted", zero_division=0)),
        "val_rec":    float(recall_score(y_val_seq, val_preds, average="weighted", zero_division=0)),
        "correct_train_count": int(np.sum(train_preds == y_train_seq)),
        "total_train":         len(y_train_seq),
        "correct_val_count":   int(np.sum(val_preds == y_val_seq)),
        "total_val":           len(y_val_seq),
        "correct_test_count":  int(np.sum(test_preds == y_test_seq)),
        "total_test":          len(y_test_seq)
    }

    predictions = {
        "train_preds": train_preds,
        "val_preds":   val_preds,
        "test_preds":  test_preds,
        "val_proba":   val_proba
    }

    trained_params = {
        "hidden_size":     hidden_size,
        "num_layers":      num_layers,
        "epochs":          epochs,
        "batch_size":      batch_size,
        "learning_rate":   learning_rate,
        "dropout":         dropout,
        "lookback_window": lookback
    }

    # ── Save model state dict ─────────────────────────────────────────────────
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path)
    logger.info(f"Saved LSTM model -> {save_path}")

    return metrics, predictions, trained_params, model
