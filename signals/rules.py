import pandas as pd
import numpy as np

class RulesEvaluator:
    def __init__(self, conditions_df: pd.DataFrame, strategy_config: dict):
        """
        Takes the True/False conditions DataFrame from conditions.py and the strategy config.
        """
        self.conditions_df = conditions_df
        self.strategy_config = strategy_config

    def get_columns_for_side(self, side: str) -> list:
        """
        Finds all columns in the DataFrame that belong to a specific side (long or short).
        Example: ['long_cond_1', 'long_cond_2']
        """
        return [col for col in self.conditions_df.columns if col.startswith(f"{side}_cond_")]

    def evaluate_and(self, columns: list) -> pd.Series:
        """
        AND Rule: All conditions must be True at the same time.
        """
        if not columns:
            return pd.Series(False, index=self.conditions_df.index)
        return self.conditions_df[columns].all(axis=1)

    def evaluate_or(self, columns: list) -> pd.Series:
        """
        OR Rule: At least one condition must be True.
        """
        if not columns:
            return pd.Series(False, index=self.conditions_df.index)
        return self.conditions_df[columns].any(axis=1)

    def evaluate_majority(self, columns: list) -> pd.Series:
        """
        Majority Rule: More than 50% of the conditions must be True.
        """
        if not columns:
            return pd.Series(False, index=self.conditions_df.index)
        total_conditions = len(columns)
        true_count = self.conditions_df[columns].sum(axis=1)
        return true_count > (total_conditions / 2)

    def evaluate_side(self, side: str) -> pd.Series:
        """
        Reads the rule from config (AND, OR, MAJORITY) and applies the correct math function.
        """
        if side not in self.strategy_config:
            return pd.Series(False, index=self.conditions_df.index)
            
        rule = self.strategy_config[side].get("rule", "AND").upper()
        columns = self.get_columns_for_side(side)
        
        if rule == "AND":
            return self.evaluate_and(columns)
        elif rule == "OR":
            return self.evaluate_or(columns)
        elif rule == "MAJORITY":
            return self.evaluate_majority(columns)
        else:
            return self.evaluate_and(columns) # Default fallback

    def generate_signals(self) -> pd.Series:
        """
        The Final Decider: Combines Long and Short evaluations to output 1, -1, or 0.
        """
        long_signals = self.evaluate_side("long")
        short_signals = self.evaluate_side("short")
        
        # Start with a column full of 0s (Hold / No Signal)
        final_signal = pd.Series(0, index=self.conditions_df.index, name="signal")
        
        # Put 1 where Long is True
        final_signal[long_signals] = 1
        
        # Put -1 where Short is True (and overwrite Long if both happen to be true to avoid confusion, 
        # or we can enforce that Long and Short can't happen at the exact same time)
        final_signal[short_signals] = -1
        
        # If both are somehow True at the exact same time, we set it back to 0 (Conflicting signals = Hold)
        final_signal[long_signals & short_signals] = 0
        
        return final_signal
