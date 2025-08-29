import datetime

def insert_script_header(script_path, version="1.0.0"):
    today = datetime.date.today().strftime("%B %d, %Y")  # Format: July 01, 2025

    header = f"""\
# =============================================================================
# Author      : Koushik Shridhar
# Date        : {today}
# Version     : {version}
#
# Description : 
#   This Python script generates UVM SystemVerilog Testbench components 
#   based on configuration provided via a CSV or structured input dictionary.
#   It creates the following:
#     - UVM top.sv
#     - test, base test, environment
#     - agents, drivers, monitors, subscribers, sequencers
#     - Sequence 
#   (Note: This script does NOT generate the RAL model, Scoreboard)
#
# CSV Format (used as input):
# -----------------------------------------------------------------------------
# Field Name   | Value(s) / Description
# -----------------------------------------------------------------------------
# DUT_NAME     | <Name of the DUT>
# NUM_INTF     | <Number of Interfaces>
# INTF         | <Name>,<Mode>,<Freq>,<ClkName>,[<RstName>,<RstType>]
#              | - Mode: M (Master) / S (Slave)
#              | - Freq: Clock frequency in MHz (e.g., 100)
#              | - RstType: active_high / active_low
#
# Example Rows:
# DUT_NAME     , usb_ctrl
# NUM_INTF     , 2
# INTF         , i2c , M , 100 , i2c_clk , [i2c_rst , active_low]
# INTF         , uart, S , 200 , uart_clk, [uart_rst, active_high]
#
# Output Summary:
#   A summary file named `README.txt` is generated under `verif/SIM/`.
#   It contains:
#     - A list of all generated files
#     - Brief descriptions for each file
#     - TODOs that guide the user to complete component logic
#
# License:
#   This script is provided "as is", without warranty of any kind.
#   You are free to modify, distribute, and use it as part of your projects.
# =============================================================================
"""

    # Read original script
    with open(script_path, "r") as f:
        original = f.read()

    # Check if already added (by checking the first few lines)
    if "Author      : Koushik Shridhar" in original.splitlines()[0:10]:
        print("⚠️  Header already exists. Skipping insertion.")
        return

    # Write updated content
    with open(script_path, "w") as f:
        f.write(header + "\n" + original)

    print(f"✅ Header inserted at top of {script_path}")


# === Example Usage ===
insert_script_header("test1.py")
insert_script_header("UVM_Tb_generator.py")

