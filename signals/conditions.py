import pandas as pd
import numpy as np

class ConditionEvaluator:
    def __init__(self, df: pd.DataFrame):
        """
        Takes the merged DataFrame containing both OHLCV data and all generated indicator columns.
        """
        self.df = df

    def get_series(self, operand) -> pd.Series:
        """
        Helper method to resolve whether an operand is a column name (string) or a static value (int/float).
        """
        if isinstance(operand, str) and operand in self.df.columns:
            return self.df[operand]
        # Return a pandas Series of the static value, matched to the dataframe index
        return pd.Series(operand, index=self.df.index)

    def evaluate_condition(self, left, operator: str, right=None) -> pd.Series:
        """
        Evaluates a single condition and returns a boolean Series.
        """
        if left is None and right is not None:
            left = right
            
        left_series = self.get_series(left)
        
        if right is not None:
            right_series = self.get_series(right)

        operator = operator.lower()

        # Basic Comparison Operators
        if operator == ">":
            return left_series > right_series
        elif operator == ">=":
            return left_series >= right_series
        elif operator == "<":
            return left_series < right_series
        elif operator == "<=":
            return left_series <= right_series
        elif operator == "==":
            return left_series == right_series
        elif operator == "!=":
            return left_series != right_series
            
        # Crossover Operators
        elif operator == "cross_above":
            # True if left was <= right previously, but is now > right
            prev_left = left_series.shift(1)
            prev_right = right_series.shift(1)
            return (prev_left <= prev_right) & (left_series > right_series)
            
        elif operator == "cross_below":
            # True if left was >= right previously, but is now < right
            prev_left = left_series.shift(1)
            prev_right = right_series.shift(1)
            return (prev_left >= prev_right) & (left_series < right_series)

        # Price Relation Operators
        elif operator == "close_above":
            return self.df["close"] > left_series
        elif operator == "close_below":
            return self.df["close"] < left_series
        elif operator == "open_above":
            return self.df["open"] > left_series
        elif operator == "open_below":
            return self.df["open"] < left_series
        elif operator == "high_above":
            return self.df["high"] > left_series
        elif operator == "high_below":
            return self.df["high"] < left_series
        elif operator == "low_above":
            return self.df["low"] > left_series
        elif operator == "low_below":
            return self.df["low"] < left_series

        # Pattern Match
        elif operator == "pattern_match" or str(left).startswith("pat_"):
            # Candlestick patterns usually output 100 or -100 when detected
            # We assume any non-zero value means the pattern is detected
            return left_series != 0

        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def apply_persist_bars(self, condition_series: pd.Series, persist_bars: int) -> pd.Series:
        """
        If a condition becomes true, it remains true for the next N bars.
        Using pandas rolling window to achieve this efficiently.
        """
        if persist_bars <= 0:
            return condition_series
            
        # A rolling max over (persist_bars + 1) will keep the 'True' (1) alive for N subsequent bars
        # Example: persist_bars = 5. A True will stay True for the current bar + 5 next bars = window of 6.
        window_size = persist_bars + 1
        persisted = condition_series.rolling(window=window_size, min_periods=1).max()
        
        # Convert back to boolean
        return persisted.astype(bool)

    def process_strategy(self, strategy_config: dict) -> pd.DataFrame:
        """
        Processes the strategy config (long/short rules) and returns a DataFrame of evaluated conditions.
        Format: Datetime index, long_cond_1, long_cond_2, short_cond_1, ...
        """
        result_df = pd.DataFrame(index=self.df.index)
        
        for side in ["long", "short"]:
            if side not in strategy_config:
                continue
                
            conditions = strategy_config[side].get("conditions", [])
            for i, cond in enumerate(conditions):
                left = cond.get("left")
                operator = cond.get("operator")
                right = cond.get("right")
                persist_bars = cond.get("persist_bars", 0)
                
                # 1. Evaluate the raw condition
                raw_series = self.evaluate_condition(left, operator, right)
                
                # 2. Apply persist_bars logic
                persisted_series = self.apply_persist_bars(raw_series, persist_bars)
                
                # 3. Store in the result DataFrame as side_cond_n (1-indexed)
                col_name = f"{side}_cond_{i+1}"
                result_df[col_name] = persisted_series
                
        return result_df
