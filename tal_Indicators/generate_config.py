import os
import pprint
import talib
from talib import abstract


def generate_config_file(output_path: str = "config.py"):
    """
    Introspects all TA-Lib functions dynamically and generates a complete config.py file
    containing inputs, outputs, and default parameters for every indicator.
    """
    funcs = talib.get_functions()
    config_dict = {}

    for name in sorted(funcs):
        info = abstract.Function(name).info

        # Flatten input names (e.g. "close" -> ["close"], ["high", "low", "close"] -> ["high", "low", "close"])
        required_cols = []
        for v in info.get("input_names", {}).values():
            if isinstance(v, str):
                required_cols.append(v)
            elif isinstance(v, (list, tuple)):
                required_cols.extend(v)

        # Build rich parameters dictionary with uniform structure (type, default, description)
        formatted_params = {}
        for p_name, default_val in info.get("parameters", {}).items():
            p_lower = p_name.lower()
            disp = info.get("display_name", name)
            if p_lower == "timeperiod":
                desc = f"Number of periods used to calculate {name.upper()}."
            elif p_lower == "fastperiod":
                desc = "Fast EMA period." if name.upper() == "MACD" else f"Fast period for {name.upper()}."
            elif p_lower == "slowperiod":
                desc = "Slow EMA period." if name.upper() == "MACD" else f"Slow period for {name.upper()}."
            elif p_lower == "signalperiod":
                desc = "Signal EMA period." if name.upper() == "MACD" else f"Signal period for {name.upper()}."
            elif "dev" in p_lower:
                desc = f"Standard deviation multiplier ({p_name})."
            elif p_lower == "matype":
                desc = f"Moving average type ({p_name})."
            else:
                desc = f"Parameter {p_name} for {disp}."

            formatted_params[p_name] = {
                "type": type(default_val).__name__,
                "default": default_val,
                "description": desc
            }

        # Build rich outputs list of dictionaries with uniform structure (name, return_type, description)
        formatted_outputs = []
        raw_outputs = list(info.get("output_names", []))
        for out_name in raw_outputs:
            mapped_name = out_name
            if out_name == "real":
                mapped_name = name.lower()
            elif out_name == "upperband":
                mapped_name = "upper_band"
            elif out_name == "middleband":
                mapped_name = "middle_band"
            elif out_name == "lowerband":
                mapped_name = "lower_band"
            elif out_name == "macdsignal":
                mapped_name = "signal"
            elif out_name == "macdhist":
                mapped_name = "histogram"

            disp = info.get("display_name", name)
            if name.upper() == "RSI" and mapped_name == "rsi":
                desc = "RSI values."
            elif name.upper() == "MACD":
                if mapped_name == "macd": desc = "MACD line."
                elif mapped_name == "signal": desc = "Signal line."
                elif mapped_name == "histogram": desc = "MACD histogram."
            elif mapped_name == "upper_band":
                desc = "Upper Bollinger Band."
            elif mapped_name == "middle_band":
                desc = "Middle Bollinger Band."
            elif mapped_name == "lower_band":
                desc = "Lower Bollinger Band."
            elif len(raw_outputs) == 1:
                desc = f"{name.upper()} values."
            else:
                desc = f"{disp} line ({mapped_name})."

            formatted_outputs.append({
                "name": mapped_name,
                "return_type": "Series",
                "description": desc
            })

        config_dict[name.upper()] = {
            "category": info.get("group", "Unknown"),
            "display_name": info.get("display_name", name),
            "talib_function": name.upper(),
            "inputs": required_cols,
            "parameters": formatted_params,
            "outputs": formatted_outputs,
        }

    # Build custom readable dictionary string
    dict_lines = ["INDICATOR_CONFIG = {"]
    for idx, (ind_name, data) in enumerate(config_dict.items()):
        dict_lines.append("")
        dict_lines.append(f'    "{ind_name}": {{')
        dict_lines.append(f'        "category": "{data["category"]}",')
        dict_lines.append(f'        "display_name": "{data["display_name"]}",')
        dict_lines.append(f'        "talib_function": "{data["talib_function"]}",')
        dict_lines.append("")
        dict_lines.append('        "inputs": [')
        for inp_idx, inp in enumerate(data["inputs"]):
            comma = "," if inp_idx < len(data["inputs"]) - 1 else ""
            dict_lines.append(f'            "{inp}"{comma}')
        dict_lines.append('        ],')
        dict_lines.append("")

        if not data["parameters"]:
            dict_lines.append('        "parameters": {},')
        else:
            dict_lines.append('        "parameters": {')
            param_items = list(data["parameters"].items())
            for p_idx, (p_name, p_info) in enumerate(param_items):
                val_str = repr(p_info["default"])
                dtype_str = p_info["type"]
                desc_str = p_info["description"]
                dict_lines.append(f'            "{p_name}": {{')
                dict_lines.append(f'                "type": "{dtype_str}",')
                dict_lines.append(f'                "default": {val_str},')
                dict_lines.append(f'                "description": "{desc_str}"')
                comma = "," if p_idx < len(param_items) - 1 else ""
                dict_lines.append(f'            }}{comma}')
            dict_lines.append('        },')

        dict_lines.append("")
        dict_lines.append('        "outputs": [')
        for out_idx, out_info in enumerate(data["outputs"]):
            dict_lines.append('            {')
            dict_lines.append(f'                "name": "{out_info["name"]}",')
            dict_lines.append(f'                "return_type": "{out_info["return_type"]}",')
            dict_lines.append(f'                "description": "{out_info["description"]}"')
            comma = "," if out_idx < len(data["outputs"]) - 1 else ""
            dict_lines.append(f'            }}{comma}')
        dict_lines.append('        ]')

        comma = "," if idx < len(config_dict) - 1 else ""
        dict_lines.append(f'    }}{comma}')
    dict_lines.append("}")

    # Format into a clean Python file string
    lines = [
        '"""',
        "Auto-generated TA-Lib Indicator Configuration File.",
        "Contains input requirements, output names, and default parameters for all TA-Lib indicators.",
        '"""',
        "",
        f"TOTAL_INDICATORS = {len(config_dict)}",
        "",
    ] + dict_lines + [
        "",
        "",
        "def get_indicator_config(name: str) -> dict:",
        '    """Returns the configuration metadata for a given indicator name."""',
        "    return INDICATOR_CONFIG.get(name.upper(), {})",
        "",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Successfully generated '{output_path}' with {len(config_dict)} indicators!")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "config.py")
    generate_config_file(output_file)
