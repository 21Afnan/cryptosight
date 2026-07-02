import pandas as pd
from cryptosight.utils.logger import get_logger

logger = get_logger("Conditions")

class ConditionEvaluator:
    def __init__(self, df: pd.DataFrame):
        """
        Takes the merged DataFrame containing both OHLCV data and all generated indicator columns.
        """
        self.df = df

    def get_series(self, operand) -> pd.Series:
        """
        Helper method to resolve whether an operand/right,left indicators name is a column name (string) or a static value (int/float).
        """
        if isinstance(operand, str) and operand in self.df.columns:
            return self.df[operand]
        # Return a pandas Series of the static value, matched to the dataframe index
        return pd.Series(operand, index=self.df.index)

    def evaluate_condition(self, left, operator: str, right=None) -> pd.Series:
        """
        Evaluates a single condition and returns a boolean Series.
        """
        operator = operator.lower()
        price_operators = {
            "close_above", "close_below",
            "open_above", "open_below",
            "high_above", "high_below",
            "low_above", "low_below"
        }

        # Consolidate price-relation operators
        if operator in price_operators:
            if left is None:
                raise ValueError(f"Condition missing required 'left' operand (operator={operator})")
            if right is not None:
                logger.warning(f"Operator '{operator}' ignores 'right' — you set right={right}, it has no effect.")
            
            price_col = operator.split("_")[0]
            direction = operator.split("_")[1]
            left_series = self.get_series(left)
            if direction == "above":
                return self.df[price_col] > left_series
            else:
                return self.df[price_col] < left_series

        # Loud error check for missing left operand
        if left is None:
            raise ValueError(f"Condition missing required 'left' operand (operator={operator})")

        left_series = self.get_series(left)
        
        if right is not None:
            right_series = self.get_series(right)

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

        # Pattern Match (requires explicit pattern_match operator)
        elif operator == "pattern_match":
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
        if persist_bars is None or persist_bars <= 0:
            return condition_series
            
        # A rolling max over (persist_bars + 1) will keep the 'True' (1) alive for N subsequent bars
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
                
            conditions = strategy_config[side].get("conditions")
            if not conditions:
                continue
                
            for i, cond in enumerate(conditions):
                left = cond.get("left")
                operator = cond.get("operator")
                right = cond.get("right")
                persist_bars = cond.get("persist_bars")
                
                # 1. Evaluate the raw condition
                raw_series = self.evaluate_condition(left, operator, right)
                
                # 2. Apply persist_bars logic
                persisted_series = self.apply_persist_bars(raw_series, persist_bars)
                
                # 3. Store in the result DataFrame as side_cond_n (1-indexed)
                col_name = f"{side}_cond_{i+1}"
                result_df[col_name] = persisted_series
                
        return result_df
