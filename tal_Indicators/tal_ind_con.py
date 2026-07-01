"""
Auto-generated TA-Lib Indicator Configuration File.
Contains input requirements, output names, and default parameters for all TA-Lib indicators.
"""

INDICATOR_CONFIG = {

    "ACOS": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric ACos",
        "talib_function": "ACOS",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "acos",
                "return_type": "Series",
                "description": "ACOS values."
            }
        ]
    },

    "AD": {
        "category": "Volume Indicators",
        "display_name": "Chaikin A/D Line",
        "talib_function": "AD",

        "inputs": [
            "high",
            "low",
            "close",
            "volume"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "ad",
                "return_type": "Series",
                "description": "AD values."
            }
        ]
    },

    "ADD": {
        "category": "Math Operators",
        "display_name": "Vector Arithmetic Add",
        "talib_function": "ADD",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "add",
                "return_type": "Series",
                "description": "ADD values."
            }
        ]
    },

    "ADOSC": {
        "category": "Volume Indicators",
        "display_name": "Chaikin A/D Oscillator",
        "talib_function": "ADOSC",

        "inputs": [
            "high",
            "low",
            "close",
            "volume"
        ],

        "parameters": {
            "fastperiod": {
                "type": "int",
                "default": 3,
                "description": "Fast period for ADOSC."
            },
            "slowperiod": {
                "type": "int",
                "default": 10,
                "description": "Slow period for ADOSC."
            }
        },

        "outputs": [
            {
                "name": "adosc",
                "return_type": "Series",
                "description": "ADOSC values."
            }
        ]
    },

    "ADX": {
        "category": "Momentum Indicators",
        "display_name": "Average Directional Movement Index",
        "talib_function": "ADX",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate ADX."
            }
        },

        "outputs": [
            {
                "name": "adx",
                "return_type": "Series",
                "description": "ADX values."
            }
        ]
    },

    "ADXR": {
        "category": "Momentum Indicators",
        "display_name": "Average Directional Movement Index Rating",
        "talib_function": "ADXR",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate ADXR."
            }
        },

        "outputs": [
            {
                "name": "adxr",
                "return_type": "Series",
                "description": "ADXR values."
            }
        ]
    },

    "APO": {
        "category": "Momentum Indicators",
        "display_name": "Absolute Price Oscillator",
        "talib_function": "APO",

        "inputs": [
            "close"
        ],

        "parameters": {
            "fastperiod": {
                "type": "int",
                "default": 12,
                "description": "Fast period for APO."
            },
            "slowperiod": {
                "type": "int",
                "default": 26,
                "description": "Slow period for APO."
            },
            "matype": {
                "type": "int",
                "default": 0,
                "description": "Moving average type (matype)."
            }
        },

        "outputs": [
            {
                "name": "apo",
                "return_type": "Series",
                "description": "APO values."
            }
        ]
    },

    "AROON": {
        "category": "Momentum Indicators",
        "display_name": "Aroon",
        "talib_function": "AROON",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate AROON."
            }
        },

        "outputs": [
            {
                "name": "aroondown",
                "return_type": "Series",
                "description": "Aroon line (aroondown)."
            },
            {
                "name": "aroonup",
                "return_type": "Series",
                "description": "Aroon line (aroonup)."
            }
        ]
    },

    "AROONOSC": {
        "category": "Momentum Indicators",
        "display_name": "Aroon Oscillator",
        "talib_function": "AROONOSC",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate AROONOSC."
            }
        },

        "outputs": [
            {
                "name": "aroonosc",
                "return_type": "Series",
                "description": "AROONOSC values."
            }
        ]
    },

    "ASIN": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric ASin",
        "talib_function": "ASIN",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "asin",
                "return_type": "Series",
                "description": "ASIN values."
            }
        ]
    },

    "ATAN": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric ATan",
        "talib_function": "ATAN",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "atan",
                "return_type": "Series",
                "description": "ATAN values."
            }
        ]
    },

    "ATR": {
        "category": "Volatility Indicators",
        "display_name": "Average True Range",
        "talib_function": "ATR",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate ATR."
            }
        },

        "outputs": [
            {
                "name": "atr",
                "return_type": "Series",
                "description": "ATR values."
            }
        ]
    },

    "AVGPRICE": {
        "category": "Price Transform",
        "display_name": "Average Price",
        "talib_function": "AVGPRICE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "avgprice",
                "return_type": "Series",
                "description": "AVGPRICE values."
            }
        ]
    },

    "BBANDS": {
        "category": "Overlap Studies",
        "display_name": "Bollinger Bands",
        "talib_function": "BBANDS",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 5,
                "description": "Number of periods used to calculate BBANDS."
            },
            "nbdevup": {
                "type": "float",
                "default": 2.0,
                "description": "Standard deviation multiplier (nbdevup)."
            },
            "nbdevdn": {
                "type": "float",
                "default": 2.0,
                "description": "Standard deviation multiplier (nbdevdn)."
            },
            "matype": {
                "type": "int",
                "default": 0,
                "description": "Moving average type (matype)."
            }
        },

        "outputs": [
            {
                "name": "upper_band",
                "return_type": "Series",
                "description": "Upper Bollinger Band."
            },
            {
                "name": "middle_band",
                "return_type": "Series",
                "description": "Middle Bollinger Band."
            },
            {
                "name": "lower_band",
                "return_type": "Series",
                "description": "Lower Bollinger Band."
            }
        ]
    },

    "BETA": {
        "category": "Statistic Functions",
        "display_name": "Beta",
        "talib_function": "BETA",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 5,
                "description": "Number of periods used to calculate BETA."
            }
        },

        "outputs": [
            {
                "name": "beta",
                "return_type": "Series",
                "description": "BETA values."
            }
        ]
    },

    "BOP": {
        "category": "Momentum Indicators",
        "display_name": "Balance Of Power",
        "talib_function": "BOP",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "bop",
                "return_type": "Series",
                "description": "BOP values."
            }
        ]
    },

    "CCI": {
        "category": "Momentum Indicators",
        "display_name": "Commodity Channel Index",
        "talib_function": "CCI",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate CCI."
            }
        },

        "outputs": [
            {
                "name": "cci",
                "return_type": "Series",
                "description": "CCI values."
            }
        ]
    },

    "CDL2CROWS": {
        "category": "Pattern Recognition",
        "display_name": "Two Crows",
        "talib_function": "CDL2CROWS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL2CROWS values."
            }
        ]
    },

    "CDL3BLACKCROWS": {
        "category": "Pattern Recognition",
        "display_name": "Three Black Crows",
        "talib_function": "CDL3BLACKCROWS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL3BLACKCROWS values."
            }
        ]
    },

    "CDL3INSIDE": {
        "category": "Pattern Recognition",
        "display_name": "Three Inside Up/Down",
        "talib_function": "CDL3INSIDE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL3INSIDE values."
            }
        ]
    },

    "CDL3LINESTRIKE": {
        "category": "Pattern Recognition",
        "display_name": "Three-Line Strike ",
        "talib_function": "CDL3LINESTRIKE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL3LINESTRIKE values."
            }
        ]
    },

    "CDL3OUTSIDE": {
        "category": "Pattern Recognition",
        "display_name": "Three Outside Up/Down",
        "talib_function": "CDL3OUTSIDE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL3OUTSIDE values."
            }
        ]
    },

    "CDL3STARSINSOUTH": {
        "category": "Pattern Recognition",
        "display_name": "Three Stars In The South",
        "talib_function": "CDL3STARSINSOUTH",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL3STARSINSOUTH values."
            }
        ]
    },

    "CDL3WHITESOLDIERS": {
        "category": "Pattern Recognition",
        "display_name": "Three Advancing White Soldiers",
        "talib_function": "CDL3WHITESOLDIERS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDL3WHITESOLDIERS values."
            }
        ]
    },

    "CDLABANDONEDBABY": {
        "category": "Pattern Recognition",
        "display_name": "Abandoned Baby",
        "talib_function": "CDLABANDONEDBABY",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.3,
                "description": "Parameter penetration for Abandoned Baby."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLABANDONEDBABY values."
            }
        ]
    },

    "CDLADVANCEBLOCK": {
        "category": "Pattern Recognition",
        "display_name": "Advance Block",
        "talib_function": "CDLADVANCEBLOCK",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLADVANCEBLOCK values."
            }
        ]
    },

    "CDLBELTHOLD": {
        "category": "Pattern Recognition",
        "display_name": "Belt-hold",
        "talib_function": "CDLBELTHOLD",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLBELTHOLD values."
            }
        ]
    },

    "CDLBREAKAWAY": {
        "category": "Pattern Recognition",
        "display_name": "Breakaway",
        "talib_function": "CDLBREAKAWAY",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLBREAKAWAY values."
            }
        ]
    },

    "CDLCLOSINGMARUBOZU": {
        "category": "Pattern Recognition",
        "display_name": "Closing Marubozu",
        "talib_function": "CDLCLOSINGMARUBOZU",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLCLOSINGMARUBOZU values."
            }
        ]
    },

    "CDLCONCEALBABYSWALL": {
        "category": "Pattern Recognition",
        "display_name": "Concealing Baby Swallow",
        "talib_function": "CDLCONCEALBABYSWALL",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLCONCEALBABYSWALL values."
            }
        ]
    },

    "CDLCOUNTERATTACK": {
        "category": "Pattern Recognition",
        "display_name": "Counterattack",
        "talib_function": "CDLCOUNTERATTACK",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLCOUNTERATTACK values."
            }
        ]
    },

    "CDLDARKCLOUDCOVER": {
        "category": "Pattern Recognition",
        "display_name": "Dark Cloud Cover",
        "talib_function": "CDLDARKCLOUDCOVER",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.5,
                "description": "Parameter penetration for Dark Cloud Cover."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLDARKCLOUDCOVER values."
            }
        ]
    },

    "CDLDOJI": {
        "category": "Pattern Recognition",
        "display_name": "Doji",
        "talib_function": "CDLDOJI",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLDOJI values."
            }
        ]
    },

    "CDLDOJISTAR": {
        "category": "Pattern Recognition",
        "display_name": "Doji Star",
        "talib_function": "CDLDOJISTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLDOJISTAR values."
            }
        ]
    },

    "CDLDRAGONFLYDOJI": {
        "category": "Pattern Recognition",
        "display_name": "Dragonfly Doji",
        "talib_function": "CDLDRAGONFLYDOJI",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLDRAGONFLYDOJI values."
            }
        ]
    },

    "CDLENGULFING": {
        "category": "Pattern Recognition",
        "display_name": "Engulfing Pattern",
        "talib_function": "CDLENGULFING",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLENGULFING values."
            }
        ]
    },

    "CDLEVENINGDOJISTAR": {
        "category": "Pattern Recognition",
        "display_name": "Evening Doji Star",
        "talib_function": "CDLEVENINGDOJISTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.3,
                "description": "Parameter penetration for Evening Doji Star."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLEVENINGDOJISTAR values."
            }
        ]
    },

    "CDLEVENINGSTAR": {
        "category": "Pattern Recognition",
        "display_name": "Evening Star",
        "talib_function": "CDLEVENINGSTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.3,
                "description": "Parameter penetration for Evening Star."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLEVENINGSTAR values."
            }
        ]
    },

    "CDLGAPSIDESIDEWHITE": {
        "category": "Pattern Recognition",
        "display_name": "Up/Down-gap side-by-side white lines",
        "talib_function": "CDLGAPSIDESIDEWHITE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLGAPSIDESIDEWHITE values."
            }
        ]
    },

    "CDLGRAVESTONEDOJI": {
        "category": "Pattern Recognition",
        "display_name": "Gravestone Doji",
        "talib_function": "CDLGRAVESTONEDOJI",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLGRAVESTONEDOJI values."
            }
        ]
    },

    "CDLHAMMER": {
        "category": "Pattern Recognition",
        "display_name": "Hammer",
        "talib_function": "CDLHAMMER",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHAMMER values."
            }
        ]
    },

    "CDLHANGINGMAN": {
        "category": "Pattern Recognition",
        "display_name": "Hanging Man",
        "talib_function": "CDLHANGINGMAN",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHANGINGMAN values."
            }
        ]
    },

    "CDLHARAMI": {
        "category": "Pattern Recognition",
        "display_name": "Harami Pattern",
        "talib_function": "CDLHARAMI",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHARAMI values."
            }
        ]
    },

    "CDLHARAMICROSS": {
        "category": "Pattern Recognition",
        "display_name": "Harami Cross Pattern",
        "talib_function": "CDLHARAMICROSS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHARAMICROSS values."
            }
        ]
    },

    "CDLHIGHWAVE": {
        "category": "Pattern Recognition",
        "display_name": "High-Wave Candle",
        "talib_function": "CDLHIGHWAVE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHIGHWAVE values."
            }
        ]
    },

    "CDLHIKKAKE": {
        "category": "Pattern Recognition",
        "display_name": "Hikkake Pattern",
        "talib_function": "CDLHIKKAKE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHIKKAKE values."
            }
        ]
    },

    "CDLHIKKAKEMOD": {
        "category": "Pattern Recognition",
        "display_name": "Modified Hikkake Pattern",
        "talib_function": "CDLHIKKAKEMOD",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHIKKAKEMOD values."
            }
        ]
    },

    "CDLHOMINGPIGEON": {
        "category": "Pattern Recognition",
        "display_name": "Homing Pigeon",
        "talib_function": "CDLHOMINGPIGEON",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLHOMINGPIGEON values."
            }
        ]
    },

    "CDLIDENTICAL3CROWS": {
        "category": "Pattern Recognition",
        "display_name": "Identical Three Crows",
        "talib_function": "CDLIDENTICAL3CROWS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLIDENTICAL3CROWS values."
            }
        ]
    },

    "CDLINNECK": {
        "category": "Pattern Recognition",
        "display_name": "In-Neck Pattern",
        "talib_function": "CDLINNECK",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLINNECK values."
            }
        ]
    },

    "CDLINVERTEDHAMMER": {
        "category": "Pattern Recognition",
        "display_name": "Inverted Hammer",
        "talib_function": "CDLINVERTEDHAMMER",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLINVERTEDHAMMER values."
            }
        ]
    },

    "CDLKICKING": {
        "category": "Pattern Recognition",
        "display_name": "Kicking",
        "talib_function": "CDLKICKING",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLKICKING values."
            }
        ]
    },

    "CDLKICKINGBYLENGTH": {
        "category": "Pattern Recognition",
        "display_name": "Kicking - bull/bear determined by the longer marubozu",
        "talib_function": "CDLKICKINGBYLENGTH",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLKICKINGBYLENGTH values."
            }
        ]
    },

    "CDLLADDERBOTTOM": {
        "category": "Pattern Recognition",
        "display_name": "Ladder Bottom",
        "talib_function": "CDLLADDERBOTTOM",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLLADDERBOTTOM values."
            }
        ]
    },

    "CDLLONGLEGGEDDOJI": {
        "category": "Pattern Recognition",
        "display_name": "Long Legged Doji",
        "talib_function": "CDLLONGLEGGEDDOJI",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLLONGLEGGEDDOJI values."
            }
        ]
    },

    "CDLLONGLINE": {
        "category": "Pattern Recognition",
        "display_name": "Long Line Candle",
        "talib_function": "CDLLONGLINE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLLONGLINE values."
            }
        ]
    },

    "CDLMARUBOZU": {
        "category": "Pattern Recognition",
        "display_name": "Marubozu",
        "talib_function": "CDLMARUBOZU",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLMARUBOZU values."
            }
        ]
    },

    "CDLMATCHINGLOW": {
        "category": "Pattern Recognition",
        "display_name": "Matching Low",
        "talib_function": "CDLMATCHINGLOW",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLMATCHINGLOW values."
            }
        ]
    },

    "CDLMATHOLD": {
        "category": "Pattern Recognition",
        "display_name": "Mat Hold",
        "talib_function": "CDLMATHOLD",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.5,
                "description": "Parameter penetration for Mat Hold."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLMATHOLD values."
            }
        ]
    },

    "CDLMORNINGDOJISTAR": {
        "category": "Pattern Recognition",
        "display_name": "Morning Doji Star",
        "talib_function": "CDLMORNINGDOJISTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.3,
                "description": "Parameter penetration for Morning Doji Star."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLMORNINGDOJISTAR values."
            }
        ]
    },

    "CDLMORNINGSTAR": {
        "category": "Pattern Recognition",
        "display_name": "Morning Star",
        "talib_function": "CDLMORNINGSTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "penetration": {
                "type": "float",
                "default": 0.3,
                "description": "Parameter penetration for Morning Star."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLMORNINGSTAR values."
            }
        ]
    },

    "CDLONNECK": {
        "category": "Pattern Recognition",
        "display_name": "On-Neck Pattern",
        "talib_function": "CDLONNECK",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLONNECK values."
            }
        ]
    },

    "CDLPIERCING": {
        "category": "Pattern Recognition",
        "display_name": "Piercing Pattern",
        "talib_function": "CDLPIERCING",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLPIERCING values."
            }
        ]
    },

    "CDLRICKSHAWMAN": {
        "category": "Pattern Recognition",
        "display_name": "Rickshaw Man",
        "talib_function": "CDLRICKSHAWMAN",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLRICKSHAWMAN values."
            }
        ]
    },

    "CDLRISEFALL3METHODS": {
        "category": "Pattern Recognition",
        "display_name": "Rising/Falling Three Methods",
        "talib_function": "CDLRISEFALL3METHODS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLRISEFALL3METHODS values."
            }
        ]
    },

    "CDLSEPARATINGLINES": {
        "category": "Pattern Recognition",
        "display_name": "Separating Lines",
        "talib_function": "CDLSEPARATINGLINES",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLSEPARATINGLINES values."
            }
        ]
    },

    "CDLSHOOTINGSTAR": {
        "category": "Pattern Recognition",
        "display_name": "Shooting Star",
        "talib_function": "CDLSHOOTINGSTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLSHOOTINGSTAR values."
            }
        ]
    },

    "CDLSHORTLINE": {
        "category": "Pattern Recognition",
        "display_name": "Short Line Candle",
        "talib_function": "CDLSHORTLINE",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLSHORTLINE values."
            }
        ]
    },

    "CDLSPINNINGTOP": {
        "category": "Pattern Recognition",
        "display_name": "Spinning Top",
        "talib_function": "CDLSPINNINGTOP",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLSPINNINGTOP values."
            }
        ]
    },

    "CDLSTALLEDPATTERN": {
        "category": "Pattern Recognition",
        "display_name": "Stalled Pattern",
        "talib_function": "CDLSTALLEDPATTERN",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLSTALLEDPATTERN values."
            }
        ]
    },

    "CDLSTICKSANDWICH": {
        "category": "Pattern Recognition",
        "display_name": "Stick Sandwich",
        "talib_function": "CDLSTICKSANDWICH",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLSTICKSANDWICH values."
            }
        ]
    },

    "CDLTAKURI": {
        "category": "Pattern Recognition",
        "display_name": "Takuri (Dragonfly Doji with very long lower shadow)",
        "talib_function": "CDLTAKURI",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLTAKURI values."
            }
        ]
    },

    "CDLTASUKIGAP": {
        "category": "Pattern Recognition",
        "display_name": "Tasuki Gap",
        "talib_function": "CDLTASUKIGAP",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLTASUKIGAP values."
            }
        ]
    },

    "CDLTHRUSTING": {
        "category": "Pattern Recognition",
        "display_name": "Thrusting Pattern",
        "talib_function": "CDLTHRUSTING",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLTHRUSTING values."
            }
        ]
    },

    "CDLTRISTAR": {
        "category": "Pattern Recognition",
        "display_name": "Tristar Pattern",
        "talib_function": "CDLTRISTAR",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLTRISTAR values."
            }
        ]
    },

    "CDLUNIQUE3RIVER": {
        "category": "Pattern Recognition",
        "display_name": "Unique 3 River",
        "talib_function": "CDLUNIQUE3RIVER",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLUNIQUE3RIVER values."
            }
        ]
    },

    "CDLUPSIDEGAP2CROWS": {
        "category": "Pattern Recognition",
        "display_name": "Upside Gap Two Crows",
        "talib_function": "CDLUPSIDEGAP2CROWS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLUPSIDEGAP2CROWS values."
            }
        ]
    },

    "CDLXSIDEGAP3METHODS": {
        "category": "Pattern Recognition",
        "display_name": "Upside/Downside Gap Three Methods",
        "talib_function": "CDLXSIDEGAP3METHODS",

        "inputs": [
            "open",
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "CDLXSIDEGAP3METHODS values."
            }
        ]
    },

    "CEIL": {
        "category": "Math Transform",
        "display_name": "Vector Ceil",
        "talib_function": "CEIL",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "ceil",
                "return_type": "Series",
                "description": "CEIL values."
            }
        ]
    },

    "CMO": {
        "category": "Momentum Indicators",
        "display_name": "Chande Momentum Oscillator",
        "talib_function": "CMO",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate CMO."
            }
        },

        "outputs": [
            {
                "name": "cmo",
                "return_type": "Series",
                "description": "CMO values."
            }
        ]
    },

    "CORREL": {
        "category": "Statistic Functions",
        "display_name": "Pearson's Correlation Coefficient (r)",
        "talib_function": "CORREL",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate CORREL."
            }
        },

        "outputs": [
            {
                "name": "correl",
                "return_type": "Series",
                "description": "CORREL values."
            }
        ]
    },

    "COS": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric Cos",
        "talib_function": "COS",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "cos",
                "return_type": "Series",
                "description": "COS values."
            }
        ]
    },

    "COSH": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric Cosh",
        "talib_function": "COSH",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "cosh",
                "return_type": "Series",
                "description": "COSH values."
            }
        ]
    },

    "DEMA": {
        "category": "Overlap Studies",
        "display_name": "Double Exponential Moving Average",
        "talib_function": "DEMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate DEMA."
            }
        },

        "outputs": [
            {
                "name": "dema",
                "return_type": "Series",
                "description": "DEMA values."
            }
        ]
    },

    "DIV": {
        "category": "Math Operators",
        "display_name": "Vector Arithmetic Div",
        "talib_function": "DIV",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "div",
                "return_type": "Series",
                "description": "DIV values."
            }
        ]
    },

    "DX": {
        "category": "Momentum Indicators",
        "display_name": "Directional Movement Index",
        "talib_function": "DX",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate DX."
            }
        },

        "outputs": [
            {
                "name": "dx",
                "return_type": "Series",
                "description": "DX values."
            }
        ]
    },

    "EMA": {
        "category": "Overlap Studies",
        "display_name": "Exponential Moving Average",
        "talib_function": "EMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate EMA."
            }
        },

        "outputs": [
            {
                "name": "ema",
                "return_type": "Series",
                "description": "EMA values."
            }
        ]
    },

    "EXP": {
        "category": "Math Transform",
        "display_name": "Vector Arithmetic Exp",
        "talib_function": "EXP",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "exp",
                "return_type": "Series",
                "description": "EXP values."
            }
        ]
    },

    "FLOOR": {
        "category": "Math Transform",
        "display_name": "Vector Floor",
        "talib_function": "FLOOR",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "floor",
                "return_type": "Series",
                "description": "FLOOR values."
            }
        ]
    },

    "HT_DCPERIOD": {
        "category": "Cycle Indicators",
        "display_name": "Hilbert Transform - Dominant Cycle Period",
        "talib_function": "HT_DCPERIOD",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "ht_dcperiod",
                "return_type": "Series",
                "description": "HT_DCPERIOD values."
            }
        ]
    },

    "HT_DCPHASE": {
        "category": "Cycle Indicators",
        "display_name": "Hilbert Transform - Dominant Cycle Phase",
        "talib_function": "HT_DCPHASE",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "ht_dcphase",
                "return_type": "Series",
                "description": "HT_DCPHASE values."
            }
        ]
    },

    "HT_PHASOR": {
        "category": "Cycle Indicators",
        "display_name": "Hilbert Transform - Phasor Components",
        "talib_function": "HT_PHASOR",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "inphase",
                "return_type": "Series",
                "description": "Hilbert Transform - Phasor Components line (inphase)."
            },
            {
                "name": "quadrature",
                "return_type": "Series",
                "description": "Hilbert Transform - Phasor Components line (quadrature)."
            }
        ]
    },

    "HT_SINE": {
        "category": "Cycle Indicators",
        "display_name": "Hilbert Transform - SineWave",
        "talib_function": "HT_SINE",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "sine",
                "return_type": "Series",
                "description": "Hilbert Transform - SineWave line (sine)."
            },
            {
                "name": "leadsine",
                "return_type": "Series",
                "description": "Hilbert Transform - SineWave line (leadsine)."
            }
        ]
    },

    "HT_TRENDLINE": {
        "category": "Overlap Studies",
        "display_name": "Hilbert Transform - Instantaneous Trendline",
        "talib_function": "HT_TRENDLINE",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "ht_trendline",
                "return_type": "Series",
                "description": "HT_TRENDLINE values."
            }
        ]
    },

    "HT_TRENDMODE": {
        "category": "Cycle Indicators",
        "display_name": "Hilbert Transform - Trend vs Cycle Mode",
        "talib_function": "HT_TRENDMODE",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "HT_TRENDMODE values."
            }
        ]
    },

    "KAMA": {
        "category": "Overlap Studies",
        "display_name": "Kaufman Adaptive Moving Average",
        "talib_function": "KAMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate KAMA."
            }
        },

        "outputs": [
            {
                "name": "kama",
                "return_type": "Series",
                "description": "KAMA values."
            }
        ]
    },

    "LINEARREG": {
        "category": "Statistic Functions",
        "display_name": "Linear Regression",
        "talib_function": "LINEARREG",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate LINEARREG."
            }
        },

        "outputs": [
            {
                "name": "linearreg",
                "return_type": "Series",
                "description": "LINEARREG values."
            }
        ]
    },

    "LINEARREG_ANGLE": {
        "category": "Statistic Functions",
        "display_name": "Linear Regression Angle",
        "talib_function": "LINEARREG_ANGLE",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate LINEARREG_ANGLE."
            }
        },

        "outputs": [
            {
                "name": "linearreg_angle",
                "return_type": "Series",
                "description": "LINEARREG_ANGLE values."
            }
        ]
    },

    "LINEARREG_INTERCEPT": {
        "category": "Statistic Functions",
        "display_name": "Linear Regression Intercept",
        "talib_function": "LINEARREG_INTERCEPT",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate LINEARREG_INTERCEPT."
            }
        },

        "outputs": [
            {
                "name": "linearreg_intercept",
                "return_type": "Series",
                "description": "LINEARREG_INTERCEPT values."
            }
        ]
    },

    "LINEARREG_SLOPE": {
        "category": "Statistic Functions",
        "display_name": "Linear Regression Slope",
        "talib_function": "LINEARREG_SLOPE",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate LINEARREG_SLOPE."
            }
        },

        "outputs": [
            {
                "name": "linearreg_slope",
                "return_type": "Series",
                "description": "LINEARREG_SLOPE values."
            }
        ]
    },

    "LN": {
        "category": "Math Transform",
        "display_name": "Vector Log Natural",
        "talib_function": "LN",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "ln",
                "return_type": "Series",
                "description": "LN values."
            }
        ]
    },

    "LOG10": {
        "category": "Math Transform",
        "display_name": "Vector Log10",
        "talib_function": "LOG10",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "log10",
                "return_type": "Series",
                "description": "LOG10 values."
            }
        ]
    },

    "MA": {
        "category": "Overlap Studies",
        "display_name": "Moving average",
        "talib_function": "MA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MA."
            },
            "matype": {
                "type": "int",
                "default": 0,
                "description": "Moving average type (matype)."
            }
        },

        "outputs": [
            {
                "name": "ma",
                "return_type": "Series",
                "description": "MA values."
            }
        ]
    },

    "MACD": {
        "category": "Momentum Indicators",
        "display_name": "Moving Average Convergence/Divergence",
        "talib_function": "MACD",

        "inputs": [
            "close"
        ],

        "parameters": {
            "fastperiod": {
                "type": "int",
                "default": 12,
                "description": "Fast EMA period."
            },
            "slowperiod": {
                "type": "int",
                "default": 26,
                "description": "Slow EMA period."
            },
            "signalperiod": {
                "type": "int",
                "default": 9,
                "description": "Signal EMA period."
            }
        },

        "outputs": [
            {
                "name": "macd",
                "return_type": "Series",
                "description": "MACD line."
            },
            {
                "name": "signal",
                "return_type": "Series",
                "description": "Signal line."
            },
            {
                "name": "histogram",
                "return_type": "Series",
                "description": "MACD histogram."
            }
        ]
    },

    "MACDEXT": {
        "category": "Momentum Indicators",
        "display_name": "MACD with controllable MA type",
        "talib_function": "MACDEXT",

        "inputs": [
            "close"
        ],

        "parameters": {
            "fastperiod": {
                "type": "int",
                "default": 12,
                "description": "Fast period for MACDEXT."
            },
            "fastmatype": {
                "type": "int",
                "default": 0,
                "description": "Parameter fastmatype for MACD with controllable MA type."
            },
            "slowperiod": {
                "type": "int",
                "default": 26,
                "description": "Slow period for MACDEXT."
            },
            "slowmatype": {
                "type": "int",
                "default": 0,
                "description": "Parameter slowmatype for MACD with controllable MA type."
            },
            "signalperiod": {
                "type": "int",
                "default": 9,
                "description": "Signal period for MACDEXT."
            },
            "signalmatype": {
                "type": "int",
                "default": 0,
                "description": "Parameter signalmatype for MACD with controllable MA type."
            }
        },

        "outputs": [
            {
                "name": "macd",
                "return_type": "Series",
                "description": "MACD with controllable MA type line (macd)."
            },
            {
                "name": "signal",
                "return_type": "Series",
                "description": "MACD with controllable MA type line (signal)."
            },
            {
                "name": "histogram",
                "return_type": "Series",
                "description": "MACD with controllable MA type line (histogram)."
            }
        ]
    },

    "MACDFIX": {
        "category": "Momentum Indicators",
        "display_name": "Moving Average Convergence/Divergence Fix 12/26",
        "talib_function": "MACDFIX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "signalperiod": {
                "type": "int",
                "default": 9,
                "description": "Signal period for MACDFIX."
            }
        },

        "outputs": [
            {
                "name": "macd",
                "return_type": "Series",
                "description": "Moving Average Convergence/Divergence Fix 12/26 line (macd)."
            },
            {
                "name": "signal",
                "return_type": "Series",
                "description": "Moving Average Convergence/Divergence Fix 12/26 line (signal)."
            },
            {
                "name": "histogram",
                "return_type": "Series",
                "description": "Moving Average Convergence/Divergence Fix 12/26 line (histogram)."
            }
        ]
    },

    "MAMA": {
        "category": "Overlap Studies",
        "display_name": "MESA Adaptive Moving Average",
        "talib_function": "MAMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "fastlimit": {
                "type": "float",
                "default": 0.5,
                "description": "Parameter fastlimit for MESA Adaptive Moving Average."
            },
            "slowlimit": {
                "type": "float",
                "default": 0.05,
                "description": "Parameter slowlimit for MESA Adaptive Moving Average."
            }
        },

        "outputs": [
            {
                "name": "mama",
                "return_type": "Series",
                "description": "MESA Adaptive Moving Average line (mama)."
            },
            {
                "name": "fama",
                "return_type": "Series",
                "description": "MESA Adaptive Moving Average line (fama)."
            }
        ]
    },

    "MAVP": {
        "category": "Overlap Studies",
        "display_name": "Moving average with variable period",
        "talib_function": "MAVP",

        "inputs": [
            "close",
            "periods"
        ],

        "parameters": {
            "minperiod": {
                "type": "int",
                "default": 2,
                "description": "Parameter minperiod for Moving average with variable period."
            },
            "maxperiod": {
                "type": "int",
                "default": 30,
                "description": "Parameter maxperiod for Moving average with variable period."
            },
            "matype": {
                "type": "int",
                "default": 0,
                "description": "Moving average type (matype)."
            }
        },

        "outputs": [
            {
                "name": "mavp",
                "return_type": "Series",
                "description": "MAVP values."
            }
        ]
    },

    "MAX": {
        "category": "Math Operators",
        "display_name": "Highest value over a specified period",
        "talib_function": "MAX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MAX."
            }
        },

        "outputs": [
            {
                "name": "max",
                "return_type": "Series",
                "description": "MAX values."
            }
        ]
    },

    "MAXINDEX": {
        "category": "Math Operators",
        "display_name": "Index of highest value over a specified period",
        "talib_function": "MAXINDEX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MAXINDEX."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "MAXINDEX values."
            }
        ]
    },

    "MEDPRICE": {
        "category": "Price Transform",
        "display_name": "Median Price",
        "talib_function": "MEDPRICE",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "medprice",
                "return_type": "Series",
                "description": "MEDPRICE values."
            }
        ]
    },

    "MFI": {
        "category": "Momentum Indicators",
        "display_name": "Money Flow Index",
        "talib_function": "MFI",

        "inputs": [
            "high",
            "low",
            "close",
            "volume"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate MFI."
            }
        },

        "outputs": [
            {
                "name": "mfi",
                "return_type": "Series",
                "description": "MFI values."
            }
        ]
    },

    "MIDPOINT": {
        "category": "Overlap Studies",
        "display_name": "MidPoint over period",
        "talib_function": "MIDPOINT",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate MIDPOINT."
            }
        },

        "outputs": [
            {
                "name": "midpoint",
                "return_type": "Series",
                "description": "MIDPOINT values."
            }
        ]
    },

    "MIDPRICE": {
        "category": "Overlap Studies",
        "display_name": "Midpoint Price over period",
        "talib_function": "MIDPRICE",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate MIDPRICE."
            }
        },

        "outputs": [
            {
                "name": "midprice",
                "return_type": "Series",
                "description": "MIDPRICE values."
            }
        ]
    },

    "MIN": {
        "category": "Math Operators",
        "display_name": "Lowest value over a specified period",
        "talib_function": "MIN",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MIN."
            }
        },

        "outputs": [
            {
                "name": "min",
                "return_type": "Series",
                "description": "MIN values."
            }
        ]
    },

    "MININDEX": {
        "category": "Math Operators",
        "display_name": "Index of lowest value over a specified period",
        "talib_function": "MININDEX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MININDEX."
            }
        },

        "outputs": [
            {
                "name": "integer",
                "return_type": "Series",
                "description": "MININDEX values."
            }
        ]
    },

    "MINMAX": {
        "category": "Math Operators",
        "display_name": "Lowest and highest values over a specified period",
        "talib_function": "MINMAX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MINMAX."
            }
        },

        "outputs": [
            {
                "name": "min",
                "return_type": "Series",
                "description": "Lowest and highest values over a specified period line (min)."
            },
            {
                "name": "max",
                "return_type": "Series",
                "description": "Lowest and highest values over a specified period line (max)."
            }
        ]
    },

    "MINMAXINDEX": {
        "category": "Math Operators",
        "display_name": "Indexes of lowest and highest values over a specified period",
        "talib_function": "MINMAXINDEX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate MINMAXINDEX."
            }
        },

        "outputs": [
            {
                "name": "minidx",
                "return_type": "Series",
                "description": "Indexes of lowest and highest values over a specified period line (minidx)."
            },
            {
                "name": "maxidx",
                "return_type": "Series",
                "description": "Indexes of lowest and highest values over a specified period line (maxidx)."
            }
        ]
    },

    "MINUS_DI": {
        "category": "Momentum Indicators",
        "display_name": "Minus Directional Indicator",
        "talib_function": "MINUS_DI",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate MINUS_DI."
            }
        },

        "outputs": [
            {
                "name": "minus_di",
                "return_type": "Series",
                "description": "MINUS_DI values."
            }
        ]
    },

    "MINUS_DM": {
        "category": "Momentum Indicators",
        "display_name": "Minus Directional Movement",
        "talib_function": "MINUS_DM",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate MINUS_DM."
            }
        },

        "outputs": [
            {
                "name": "minus_dm",
                "return_type": "Series",
                "description": "MINUS_DM values."
            }
        ]
    },

    "MOM": {
        "category": "Momentum Indicators",
        "display_name": "Momentum",
        "talib_function": "MOM",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 10,
                "description": "Number of periods used to calculate MOM."
            }
        },

        "outputs": [
            {
                "name": "mom",
                "return_type": "Series",
                "description": "MOM values."
            }
        ]
    },

    "MULT": {
        "category": "Math Operators",
        "display_name": "Vector Arithmetic Mult",
        "talib_function": "MULT",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "mult",
                "return_type": "Series",
                "description": "MULT values."
            }
        ]
    },

    "NATR": {
        "category": "Volatility Indicators",
        "display_name": "Normalized Average True Range",
        "talib_function": "NATR",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate NATR."
            }
        },

        "outputs": [
            {
                "name": "natr",
                "return_type": "Series",
                "description": "NATR values."
            }
        ]
    },

    "OBV": {
        "category": "Volume Indicators",
        "display_name": "On Balance Volume",
        "talib_function": "OBV",

        "inputs": [
            "close",
            "volume"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "obv",
                "return_type": "Series",
                "description": "OBV values."
            }
        ]
    },

    "PLUS_DI": {
        "category": "Momentum Indicators",
        "display_name": "Plus Directional Indicator",
        "talib_function": "PLUS_DI",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate PLUS_DI."
            }
        },

        "outputs": [
            {
                "name": "plus_di",
                "return_type": "Series",
                "description": "PLUS_DI values."
            }
        ]
    },

    "PLUS_DM": {
        "category": "Momentum Indicators",
        "display_name": "Plus Directional Movement",
        "talib_function": "PLUS_DM",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate PLUS_DM."
            }
        },

        "outputs": [
            {
                "name": "plus_dm",
                "return_type": "Series",
                "description": "PLUS_DM values."
            }
        ]
    },

    "PPO": {
        "category": "Momentum Indicators",
        "display_name": "Percentage Price Oscillator",
        "talib_function": "PPO",

        "inputs": [
            "close"
        ],

        "parameters": {
            "fastperiod": {
                "type": "int",
                "default": 12,
                "description": "Fast period for PPO."
            },
            "slowperiod": {
                "type": "int",
                "default": 26,
                "description": "Slow period for PPO."
            },
            "matype": {
                "type": "int",
                "default": 0,
                "description": "Moving average type (matype)."
            }
        },

        "outputs": [
            {
                "name": "ppo",
                "return_type": "Series",
                "description": "PPO values."
            }
        ]
    },

    "ROC": {
        "category": "Momentum Indicators",
        "display_name": "Rate of change : ((price/prevPrice)-1)*100",
        "talib_function": "ROC",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 10,
                "description": "Number of periods used to calculate ROC."
            }
        },

        "outputs": [
            {
                "name": "roc",
                "return_type": "Series",
                "description": "ROC values."
            }
        ]
    },

    "ROCP": {
        "category": "Momentum Indicators",
        "display_name": "Rate of change Percentage: (price-prevPrice)/prevPrice",
        "talib_function": "ROCP",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 10,
                "description": "Number of periods used to calculate ROCP."
            }
        },

        "outputs": [
            {
                "name": "rocp",
                "return_type": "Series",
                "description": "ROCP values."
            }
        ]
    },

    "ROCR": {
        "category": "Momentum Indicators",
        "display_name": "Rate of change ratio: (price/prevPrice)",
        "talib_function": "ROCR",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 10,
                "description": "Number of periods used to calculate ROCR."
            }
        },

        "outputs": [
            {
                "name": "rocr",
                "return_type": "Series",
                "description": "ROCR values."
            }
        ]
    },

    "ROCR100": {
        "category": "Momentum Indicators",
        "display_name": "Rate of change ratio 100 scale: (price/prevPrice)*100",
        "talib_function": "ROCR100",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 10,
                "description": "Number of periods used to calculate ROCR100."
            }
        },

        "outputs": [
            {
                "name": "rocr100",
                "return_type": "Series",
                "description": "ROCR100 values."
            }
        ]
    },

    "RSI": {
        "category": "Momentum Indicators",
        "display_name": "Relative Strength Index",
        "talib_function": "RSI",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate RSI."
            }
        },

        "outputs": [
            {
                "name": "rsi",
                "return_type": "Series",
                "description": "RSI values."
            }
        ]
    },

    "SAR": {
        "category": "Overlap Studies",
        "display_name": "Parabolic SAR",
        "talib_function": "SAR",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "acceleration": {
                "type": "float",
                "default": 0.02,
                "description": "Parameter acceleration for Parabolic SAR."
            },
            "maximum": {
                "type": "float",
                "default": 0.2,
                "description": "Parameter maximum for Parabolic SAR."
            }
        },

        "outputs": [
            {
                "name": "sar",
                "return_type": "Series",
                "description": "SAR values."
            }
        ]
    },

    "SAREXT": {
        "category": "Overlap Studies",
        "display_name": "Parabolic SAR - Extended",
        "talib_function": "SAREXT",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {
            "startvalue": {
                "type": "float",
                "default": 0.0,
                "description": "Parameter startvalue for Parabolic SAR - Extended."
            },
            "offsetonreverse": {
                "type": "float",
                "default": 0.0,
                "description": "Parameter offsetonreverse for Parabolic SAR - Extended."
            },
            "accelerationinitlong": {
                "type": "float",
                "default": 0.02,
                "description": "Parameter accelerationinitlong for Parabolic SAR - Extended."
            },
            "accelerationlong": {
                "type": "float",
                "default": 0.02,
                "description": "Parameter accelerationlong for Parabolic SAR - Extended."
            },
            "accelerationmaxlong": {
                "type": "float",
                "default": 0.2,
                "description": "Parameter accelerationmaxlong for Parabolic SAR - Extended."
            },
            "accelerationinitshort": {
                "type": "float",
                "default": 0.02,
                "description": "Parameter accelerationinitshort for Parabolic SAR - Extended."
            },
            "accelerationshort": {
                "type": "float",
                "default": 0.02,
                "description": "Parameter accelerationshort for Parabolic SAR - Extended."
            },
            "accelerationmaxshort": {
                "type": "float",
                "default": 0.2,
                "description": "Parameter accelerationmaxshort for Parabolic SAR - Extended."
            }
        },

        "outputs": [
            {
                "name": "sarext",
                "return_type": "Series",
                "description": "SAREXT values."
            }
        ]
    },

    "SIN": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric Sin",
        "talib_function": "SIN",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "sin",
                "return_type": "Series",
                "description": "SIN values."
            }
        ]
    },

    "SINH": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric Sinh",
        "talib_function": "SINH",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "sinh",
                "return_type": "Series",
                "description": "SINH values."
            }
        ]
    },

    "SMA": {
        "category": "Overlap Studies",
        "display_name": "Simple Moving Average",
        "talib_function": "SMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate SMA."
            }
        },

        "outputs": [
            {
                "name": "sma",
                "return_type": "Series",
                "description": "SMA values."
            }
        ]
    },

    "SQRT": {
        "category": "Math Transform",
        "display_name": "Vector Square Root",
        "talib_function": "SQRT",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "sqrt",
                "return_type": "Series",
                "description": "SQRT values."
            }
        ]
    },

    "STDDEV": {
        "category": "Statistic Functions",
        "display_name": "Standard Deviation",
        "talib_function": "STDDEV",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 5,
                "description": "Number of periods used to calculate STDDEV."
            },
            "nbdev": {
                "type": "float",
                "default": 1.0,
                "description": "Standard deviation multiplier (nbdev)."
            }
        },

        "outputs": [
            {
                "name": "stddev",
                "return_type": "Series",
                "description": "STDDEV values."
            }
        ]
    },

    "STOCH": {
        "category": "Momentum Indicators",
        "display_name": "Stochastic",
        "talib_function": "STOCH",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "fastk_period": {
                "type": "int",
                "default": 5,
                "description": "Parameter fastk_period for Stochastic."
            },
            "slowk_period": {
                "type": "int",
                "default": 3,
                "description": "Parameter slowk_period for Stochastic."
            },
            "slowk_matype": {
                "type": "int",
                "default": 0,
                "description": "Parameter slowk_matype for Stochastic."
            },
            "slowd_period": {
                "type": "int",
                "default": 3,
                "description": "Parameter slowd_period for Stochastic."
            },
            "slowd_matype": {
                "type": "int",
                "default": 0,
                "description": "Parameter slowd_matype for Stochastic."
            }
        },

        "outputs": [
            {
                "name": "slowk",
                "return_type": "Series",
                "description": "Stochastic line (slowk)."
            },
            {
                "name": "slowd",
                "return_type": "Series",
                "description": "Stochastic line (slowd)."
            }
        ]
    },

    "STOCHF": {
        "category": "Momentum Indicators",
        "display_name": "Stochastic Fast",
        "talib_function": "STOCHF",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "fastk_period": {
                "type": "int",
                "default": 5,
                "description": "Parameter fastk_period for Stochastic Fast."
            },
            "fastd_period": {
                "type": "int",
                "default": 3,
                "description": "Parameter fastd_period for Stochastic Fast."
            },
            "fastd_matype": {
                "type": "int",
                "default": 0,
                "description": "Parameter fastd_matype for Stochastic Fast."
            }
        },

        "outputs": [
            {
                "name": "fastk",
                "return_type": "Series",
                "description": "Stochastic Fast line (fastk)."
            },
            {
                "name": "fastd",
                "return_type": "Series",
                "description": "Stochastic Fast line (fastd)."
            }
        ]
    },

    "STOCHRSI": {
        "category": "Momentum Indicators",
        "display_name": "Stochastic Relative Strength Index",
        "talib_function": "STOCHRSI",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate STOCHRSI."
            },
            "fastk_period": {
                "type": "int",
                "default": 5,
                "description": "Parameter fastk_period for Stochastic Relative Strength Index."
            },
            "fastd_period": {
                "type": "int",
                "default": 3,
                "description": "Parameter fastd_period for Stochastic Relative Strength Index."
            },
            "fastd_matype": {
                "type": "int",
                "default": 0,
                "description": "Parameter fastd_matype for Stochastic Relative Strength Index."
            }
        },

        "outputs": [
            {
                "name": "fastk",
                "return_type": "Series",
                "description": "Stochastic Relative Strength Index line (fastk)."
            },
            {
                "name": "fastd",
                "return_type": "Series",
                "description": "Stochastic Relative Strength Index line (fastd)."
            }
        ]
    },

    "SUB": {
        "category": "Math Operators",
        "display_name": "Vector Arithmetic Subtraction",
        "talib_function": "SUB",

        "inputs": [
            "high",
            "low"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "sub",
                "return_type": "Series",
                "description": "SUB values."
            }
        ]
    },

    "SUM": {
        "category": "Math Operators",
        "display_name": "Summation",
        "talib_function": "SUM",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate SUM."
            }
        },

        "outputs": [
            {
                "name": "sum",
                "return_type": "Series",
                "description": "SUM values."
            }
        ]
    },

    "T3": {
        "category": "Overlap Studies",
        "display_name": "Triple Exponential Moving Average (T3)",
        "talib_function": "T3",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 5,
                "description": "Number of periods used to calculate T3."
            },
            "vfactor": {
                "type": "float",
                "default": 0.7,
                "description": "Parameter vfactor for Triple Exponential Moving Average (T3)."
            }
        },

        "outputs": [
            {
                "name": "t3",
                "return_type": "Series",
                "description": "T3 values."
            }
        ]
    },

    "TAN": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric Tan",
        "talib_function": "TAN",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "tan",
                "return_type": "Series",
                "description": "TAN values."
            }
        ]
    },

    "TANH": {
        "category": "Math Transform",
        "display_name": "Vector Trigonometric Tanh",
        "talib_function": "TANH",

        "inputs": [
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "tanh",
                "return_type": "Series",
                "description": "TANH values."
            }
        ]
    },

    "TEMA": {
        "category": "Overlap Studies",
        "display_name": "Triple Exponential Moving Average",
        "talib_function": "TEMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate TEMA."
            }
        },

        "outputs": [
            {
                "name": "tema",
                "return_type": "Series",
                "description": "TEMA values."
            }
        ]
    },

    "TRANGE": {
        "category": "Volatility Indicators",
        "display_name": "True Range",
        "talib_function": "TRANGE",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "trange",
                "return_type": "Series",
                "description": "TRANGE values."
            }
        ]
    },

    "TRIMA": {
        "category": "Overlap Studies",
        "display_name": "Triangular Moving Average",
        "talib_function": "TRIMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate TRIMA."
            }
        },

        "outputs": [
            {
                "name": "trima",
                "return_type": "Series",
                "description": "TRIMA values."
            }
        ]
    },

    "TRIX": {
        "category": "Momentum Indicators",
        "display_name": "1-day Rate-Of-Change (ROC) of a Triple Smooth EMA",
        "talib_function": "TRIX",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate TRIX."
            }
        },

        "outputs": [
            {
                "name": "trix",
                "return_type": "Series",
                "description": "TRIX values."
            }
        ]
    },

    "TSF": {
        "category": "Statistic Functions",
        "display_name": "Time Series Forecast",
        "talib_function": "TSF",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate TSF."
            }
        },

        "outputs": [
            {
                "name": "tsf",
                "return_type": "Series",
                "description": "TSF values."
            }
        ]
    },

    "TYPPRICE": {
        "category": "Price Transform",
        "display_name": "Typical Price",
        "talib_function": "TYPPRICE",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "typprice",
                "return_type": "Series",
                "description": "TYPPRICE values."
            }
        ]
    },

    "ULTOSC": {
        "category": "Momentum Indicators",
        "display_name": "Ultimate Oscillator",
        "talib_function": "ULTOSC",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod1": {
                "type": "int",
                "default": 7,
                "description": "Parameter timeperiod1 for Ultimate Oscillator."
            },
            "timeperiod2": {
                "type": "int",
                "default": 14,
                "description": "Parameter timeperiod2 for Ultimate Oscillator."
            },
            "timeperiod3": {
                "type": "int",
                "default": 28,
                "description": "Parameter timeperiod3 for Ultimate Oscillator."
            }
        },

        "outputs": [
            {
                "name": "ultosc",
                "return_type": "Series",
                "description": "ULTOSC values."
            }
        ]
    },

    "VAR": {
        "category": "Statistic Functions",
        "display_name": "Variance",
        "talib_function": "VAR",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 5,
                "description": "Number of periods used to calculate VAR."
            },
            "nbdev": {
                "type": "float",
                "default": 1.0,
                "description": "Standard deviation multiplier (nbdev)."
            }
        },

        "outputs": [
            {
                "name": "var",
                "return_type": "Series",
                "description": "VAR values."
            }
        ]
    },

    "WCLPRICE": {
        "category": "Price Transform",
        "display_name": "Weighted Close Price",
        "talib_function": "WCLPRICE",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {},

        "outputs": [
            {
                "name": "wclprice",
                "return_type": "Series",
                "description": "WCLPRICE values."
            }
        ]
    },

    "WILLR": {
        "category": "Momentum Indicators",
        "display_name": "Williams' %R",
        "talib_function": "WILLR",

        "inputs": [
            "high",
            "low",
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 14,
                "description": "Number of periods used to calculate WILLR."
            }
        },

        "outputs": [
            {
                "name": "willr",
                "return_type": "Series",
                "description": "WILLR values."
            }
        ]
    },

    "WMA": {
        "category": "Overlap Studies",
        "display_name": "Weighted Moving Average",
        "talib_function": "WMA",

        "inputs": [
            "close"
        ],

        "parameters": {
            "timeperiod": {
                "type": "int",
                "default": 30,
                "description": "Number of periods used to calculate WMA."
            }
        },

        "outputs": [
            {
                "name": "wma",
                "return_type": "Series",
                "description": "WMA values."
            }
        ]
    }
}


def get_indicator_config(name: str) -> dict:
    """Returns the configuration metadata for a given indicator name."""
    return INDICATOR_CONFIG.get(name.upper(), {})
