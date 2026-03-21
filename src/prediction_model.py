"""Demand forecasting model for the bakery.

Trains a GradientBoostingRegressor on historical sales data with features
including day-of-week, weather, holidays, and lag/rolling sales.

Usage:
    python -m src.prediction_model          # Train + predict next 3 days
    python -m src.prediction_model --train   # Only train (save model)
    python -m src.prediction_model --predict  # Only predict (load model)
"""

import math
import pickle
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

DB_PATH = Path(__file__).parent.parent / "bakery.db"
MODEL_PATH = Path(__file__).parent.parent / "model.pkl"

# ---------------------------------------------------------------------------
# German holidays (Bavaria) — extend as needed
# ---------------------------------------------------------------------------
GERMAN_HOLIDAYS = {
    "2025-12-24", "2025-12-25", "2025-12-26",
    "2025-12-31", "2026-01-01", "2026-01-06",
    "2026-02-16", "2026-02-17",
    "2026-04-03", "2026-04-06",
    "2026-05-01", "2026-05-14",
    "2026-05-25", "2026-06-04",
    "2026-08-15", "2026-10-03",
    "2026-11-01", "2026-12-25", "2026-12-26",
}


def _weather_code_group(code: int | None) -> int:
    """Map WMO weather code to simplified group: 0=clear, 1=cloudy, 2=rain, 3=snow."""
    if code is None:
        return 0
    if code <= 1:
        return 0  # clear
    if code <= 3:
        return 1  # cloudy
    if code <= 67:
        return 2  # rain/drizzle/fog
    return 3  # snow


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _days_to_nearest_holiday(d: date) -> int:
    """Distance in days to the nearest holiday (past or future, within 30 days)."""
    min_dist = 30
    for h in GERMAN_HOLIDAYS:
        hd = date.fromisoformat(h)
        dist = abs((hd - d).days)
        if dist < min_dist:
            min_dist = dist
    return min_dist


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_training_data() -> pd.DataFrame:
    """Load sales + weather + product info and engineer features."""
    conn = _get_connection()

    # Sales
    sales_df = pd.read_sql_query(
        "SELECT s.sale_date, s.product_id, s.quantity_sold, bg.name AS product_name "
        "FROM sales s JOIN baked_goods bg ON s.product_id = bg.id "
        "ORDER BY s.sale_date",
        conn,
    )

    # Weather
    weather_df = pd.read_sql_query(
        "SELECT weather_date AS sale_date, temperature_max, temperature_min, "
        "temperature_mean, precipitation_mm, weather_code FROM weather_data",
        conn,
    )

    conn.close()

    if sales_df.empty:
        return pd.DataFrame()

    # Merge
    df = sales_df.merge(weather_df, on="sale_date", how="left")

    # Fill missing weather with defaults
    df["temperature_mean"] = df["temperature_mean"].fillna(5.0)
    df["temperature_max"] = df["temperature_max"].fillna(8.0)
    df["precipitation_mm"] = df["precipitation_mm"].fillna(0.0)
    df["weather_code"] = df["weather_code"].fillna(0)

    # Date features
    df["date_parsed"] = pd.to_datetime(df["sale_date"])
    df["day_of_week"] = df["date_parsed"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["week_of_year"] = df["date_parsed"].dt.isocalendar().week.astype(int)
    df["is_holiday"] = df["sale_date"].isin(GERMAN_HOLIDAYS).astype(int)
    df["days_to_holiday"] = df["date_parsed"].apply(
        lambda x: _days_to_nearest_holiday(x.date())
    )
    df["weather_group"] = df["weather_code"].apply(_weather_code_group)

    # Sort for lag computation
    df = df.sort_values(["product_id", "sale_date"]).reset_index(drop=True)

    # Lag features per product
    for pid in df["product_id"].unique():
        mask = df["product_id"] == pid
        sub = df.loc[mask, "quantity_sold"]
        df.loc[mask, "sales_lag_1"] = sub.shift(1)
        df.loc[mask, "sales_lag_7"] = sub.shift(7)
        df.loc[mask, "sales_rolling_7_mean"] = sub.shift(1).rolling(7, min_periods=1).mean()

    # Fill NaN lags with column median
    for col in ["sales_lag_1", "sales_lag_7", "sales_rolling_7_mean"]:
        df[col] = df[col].fillna(df[col].median() if not df[col].isna().all() else 0)

    return df


FEATURE_COLS = [
    "product_id", "day_of_week", "is_weekend", "is_holiday", "week_of_year",
    "days_to_holiday", "temperature_mean", "temperature_max", "precipitation_mm",
    "weather_group", "sales_lag_1", "sales_lag_7", "sales_rolling_7_mean",
]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model() -> GradientBoostingRegressor:
    """Train a GBR model on all historical sales data."""
    df = load_training_data()
    if df.empty:
        raise ValueError("No training data found. Run seed_fake_data.py first.")

    X = df[FEATURE_COLS].values
    y = df["quantity_sold"].values

    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        min_samples_leaf=5,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X, y)

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    # Print training score
    train_score = model.score(X, y)
    print(f"  Model trained: R² = {train_score:.4f}, {len(y)} samples")
    print(f"  Model saved to: {MODEL_PATH}")

    return model


def load_model() -> GradientBoostingRegressor:
    """Load saved model from disk."""
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def generate_predictions(model: GradientBoostingRegressor, days: int = 3) -> int:
    """Generate predictions for the next N days for all products.

    Returns number of predictions generated.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Get all products
    cursor.execute("SELECT id, name FROM baked_goods")
    products = [(row["id"], row["name"]) for row in cursor.fetchall()]

    # Get recent sales for lag features
    cutoff = (date.today() - timedelta(days=14)).isoformat()
    cursor.execute(
        "SELECT product_id, sale_date, quantity_sold FROM sales "
        "WHERE sale_date >= ? ORDER BY sale_date",
        (cutoff,),
    )
    recent_sales: dict[int, list[tuple[str, int]]] = {}
    for row in cursor.fetchall():
        recent_sales.setdefault(row["product_id"], []).append(
            (row["sale_date"], row["quantity_sold"])
        )

    # Get weather for prediction dates
    today = date.today()
    pred_dates = [(today + timedelta(days=i)) for i in range(days)]

    cursor.execute(
        "SELECT weather_date, temperature_max, temperature_mean, "
        "precipitation_mm, weather_code "
        "FROM weather_data WHERE weather_date BETWEEN ? AND ?",
        (pred_dates[0].isoformat(), pred_dates[-1].isoformat()),
    )
    weather_map: dict[str, dict] = {}
    for row in cursor.fetchall():
        weather_map[row["weather_date"]] = {
            "temperature_max": row["temperature_max"] or 8.0,
            "temperature_mean": row["temperature_mean"] or 5.0,
            "precipitation_mm": row["precipitation_mm"] or 0.0,
            "weather_code": row["weather_code"] or 0,
        }

    count = 0
    for prod_id, prod_name in products:
        sales_list = recent_sales.get(prod_id, [])
        qtys = [q for _, q in sales_list]

        for pred_date in pred_dates:
            ds = pred_date.isoformat()
            w = weather_map.get(ds, {
                "temperature_max": 8.0, "temperature_mean": 5.0,
                "precipitation_mm": 0.0, "weather_code": 0,
            })

            # Compute lag features
            lag_1 = qtys[-1] if qtys else 50
            lag_7 = qtys[-7] if len(qtys) >= 7 else (qtys[-1] if qtys else 50)
            rolling_7 = np.mean(qtys[-7:]) if qtys else 50

            features = np.array([[
                prod_id,
                pred_date.weekday(),
                int(pred_date.weekday() >= 5),
                int(ds in GERMAN_HOLIDAYS),
                pred_date.isocalendar()[1],
                _days_to_nearest_holiday(pred_date),
                w["temperature_mean"],
                w["temperature_max"],
                w["precipitation_mm"],
                _weather_code_group(w["weather_code"]),
                lag_1,
                lag_7,
                rolling_7,
            ]])

            predicted = max(1, round(model.predict(features)[0]))
            recommended = max(5, math.ceil(predicted * 1.10))
            conf_lower = max(1, round(predicted * 0.80))
            conf_upper = round(predicted * 1.20)

            cursor.execute(
                "INSERT INTO predictions "
                "(prediction_date, product_id, predicted_sales, recommended_production, "
                "confidence_lower, confidence_upper, model_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(prediction_date, product_id) DO UPDATE SET "
                "predicted_sales=excluded.predicted_sales, "
                "recommended_production=excluded.recommended_production, "
                "confidence_lower=excluded.confidence_lower, "
                "confidence_upper=excluded.confidence_upper, "
                "model_version=excluded.model_version, "
                "created_at=CURRENT_TIMESTAMP",
                (ds, prod_id, predicted, recommended,
                 conf_lower, conf_upper, "gbr-v1"),
            )
            count += 1

            # Append predicted to qtys for next-day lag
            qtys.append(predicted)

    conn.commit()
    conn.close()
    return count


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    train_only = "--train" in sys.argv
    predict_only = "--predict" in sys.argv

    if predict_only:
        print("Loading saved model ...")
        model = load_model()
    else:
        print("Training model ...")
        model = train_model()
        if train_only:
            return

    print("Generating predictions ...")
    count = generate_predictions(model, days=3)
    print(f"  {count} predictions stored")
    print("Done!")


if __name__ == "__main__":
    main()
