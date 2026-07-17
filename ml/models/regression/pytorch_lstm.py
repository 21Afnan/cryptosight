from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from cryptosight.utils.logger import get_logger

logger = get_logger("PyTorchLSTM")


class LSTMNet(nn.Module):
    """
    LSTM Neural Network for financial return regression.
    Input shape: (batch, seq_len, features)
    Output shape: (batch,) — one return prediction per sequence
    """

    def __init__(self, input_size, hidden_size, num_layers, dropout=0.0):
        super(LSTMNet, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        # Take only the last timestep's output
        output = self.fc(lstm_out[:, -1, :])
        return output.squeeze(-1)


def build_sequences(X: np.ndarray, y: np.ndarray, lookback: int):
    """
    Converts flat tabular arrays into LSTM sequences using a sliding window.

    For each index i starting from `lookback`:
        - X_seq[i] = X[i - lookback : i]   shape: (lookback, features)
        - y_seq[i] = y[i]                   the return to predict at step i

    Returns:
        X_seq: np.ndarray of shape (N - lookback, lookback, features)
        y_seq: np.ndarray of shape (N - lookback,)
    """
    X_seqs = []
    y_seqs = []
    for i in range(lookback, len(X)):
        X_seqs.append(X[i - lookback: i])   # past `lookback` bars
        y_seqs.append(y[i])                 # target at current bar
    return np.array(X_seqs, dtype=np.float32), np.array(y_seqs, dtype=np.float32)


def train_pytorch_lstm_regressor(X_train, y_train, X_val, y_val, X_test, y_test, params, save_path):
    """
    Train a PyTorch LSTM regressor with proper time-series sequences.
    Called directly from RegressorPipeline when model_name == 'lstm_regressor'.

    Sliding window of `lookback_window` past bars is built per split before training.

    Returns:
        metrics        - dict of RMSE/MAE/R2 for train/val/test
        predictions    - dict of train_preds / val_preds / test_preds
        trained_params - hyperparams dict for JSON
        model          - the trained LSTMNet instance
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
        f"Training LSTM Regressor | Device: {device} | "
        f"Hidden: {hidden_size} | Layers: {num_layers} | "
        f"Lookback: {lookback} | Epochs: {epochs}"
    )

    # ── Build sliding window sequences ───────────────────────────────────────
    # Each sample is now a real temporal sequence of `lookback` past candles
    X_train_seq, y_train_seq = build_sequences(X_train, y_train, lookback)
    X_val_seq,   y_val_seq   = build_sequences(X_val,   y_val,   lookback)
    X_test_seq,  y_test_seq  = build_sequences(X_test,  y_test,  lookback)

    logger.info(
        f"Sequence shapes | Train: {X_train_seq.shape} | "
        f"Val: {X_val_seq.shape} | Test: {X_test_seq.shape}"
    )

    input_size = X_train_seq.shape[2]   # number of features
    model = LSTMNet(input_size, hidden_size, num_layers, dropout).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn   = nn.MSELoss()

    # ── Training loop ─────────────────────────────────────────────────────────
    dataset = TensorDataset(
        torch.tensor(X_train_seq, dtype=torch.float32),
        torch.tensor(y_train_seq, dtype=torch.float32)
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in loader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_X)
            loss  = loss_fn(preds, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(f"  Epoch [{epoch+1}/{epochs}] Loss: {epoch_loss / len(loader):.6f}")

    # ── Predict on all splits ─────────────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        train_preds = model(torch.tensor(X_train_seq, dtype=torch.float32).to(device)).cpu().numpy()
        val_preds   = model(torch.tensor(X_val_seq,   dtype=torch.float32).to(device)).cpu().numpy()
        test_preds  = model(torch.tensor(X_test_seq,  dtype=torch.float32).to(device)).cpu().numpy()

    # ── Metrics (computed on sequenced targets) ───────────────────────────────
    metrics = {
        "train_rmse":  round(float(np.sqrt(mean_squared_error(y_train_seq, train_preds))), 6),
        "val_rmse":    round(float(np.sqrt(mean_squared_error(y_val_seq,   val_preds))),   6),
        "test_rmse":   round(float(np.sqrt(mean_squared_error(y_test_seq,  test_preds))),  6),
        "train_mae":   round(float(mean_absolute_error(y_train_seq, train_preds)), 6),
        "val_mae":     round(float(mean_absolute_error(y_val_seq,   val_preds)),   6),
        "test_mae":    round(float(mean_absolute_error(y_test_seq,  test_preds)),  6),
        "train_r2":    round(float(r2_score(y_train_seq, train_preds)), 4),
        "val_r2":      round(float(r2_score(y_val_seq,   val_preds)),   4),
        "test_r2":     round(float(r2_score(y_test_seq,  test_preds)),  4),
        "total_train": int(len(y_train_seq)),
        "total_val":   int(len(y_val_seq)),
        "total_test":  int(len(y_test_seq))
    }

    predictions = {
        "train_preds": train_preds,
        "val_preds":   val_preds,
        "test_preds":  test_preds
    }

    trained_params = {
        "hidden_size":    hidden_size,
        "num_layers":     num_layers,
        "epochs":         epochs,
        "batch_size":     batch_size,
        "learning_rate":  learning_rate,
        "dropout":        dropout,
        "lookback_window": lookback
    }

    # ── Save model state dict ─────────────────────────────────────────────────
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), save_path)
    logger.info(f"Saved LSTM model -> {save_path}")

    return metrics, predictions, trained_params, model
