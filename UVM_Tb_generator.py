# =============================================================================
# Author      : Koushik Shridhar
# Date        : July 06, 2025
# Version     : 1.0.0
#
# Description : 
#   This Python script generates UVM SystemVerilog Testbench components 
#   based on configuration provided via a CSV or structured input dictionary.
#   It creates the following:
#     - UVM top.sv
#     - test, base test, environment
#     - agents, drivers, monitors, subscribers, sequencers
#     - Sequence stubs
#   (Note: This script does NOT generate the RAL model.)
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

import csv
import os
import sys
import textwrap

# Open a log file to capture all print output
log_file_name = "Py_log.txt"
log_file = open( log_file_name, "w")
sys.stdout = log_file
sys.stderr = log_file  # Optional: Also capture errors

import platform
from datetime import datetime

# === Setup logging ===
class Logger(object):
    def __init__(self, file):
        self.terminal = sys.__stdout__
        self.log = open(file, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger(log_file_name)
sys.stderr = sys.stdout

# === Log Header ===
print(f">> Log started at: {datetime.now()} <<")
print(f">> Python version: {platform.python_version()} ({sys.executable}) <<\n")

CSV_FILE = "UVM_TB_PARAMS.csv"
OUTPUT_DIR = "verif"

def read_interface_csv(filename):
    config = {}
    interfaces = []

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Clean up row values
            row = [cell.strip() for cell in row if cell.strip()]
            if not row:
                continue

            key = row[0].upper().replace(" ", "_")

            if key == "DUT_NAME" and len(row) >= 2:
                config["dut_name"] = row[1]

            elif key == "NUM_INTF" and len(row) >= 2:
                config["num_interfaces"] = int(row[1])

            elif key == "INTF" and len(row) >= 5:
                interface = {
                    "name": row[1],
                    "mode": row[2],
                    "speed": row[3],
                    "clk": row[4]
                }

                # === Optional reset info ===
                if len(row) >= 6 and ',' in row[5]:
                    rst_fields = row[5].split(',')
                    interface["rst"] = rst_fields[0].strip()
                    interface["rst_type"] = rst_fields[1].strip() if len(rst_fields) > 1 else "1"  # default to active-high
                elif len(row) >= 6:
                    interface["rst"] = row[5].strip()
                    interface["rst_type"] = "1"  # default active-high
                else:
                    interface["rst"] = None
                    interface["rst_type"] = None

                interfaces.append(interface)

    config["interfaces"] = interfaces
    return config


config = read_interface_csv(CSV_FILE)

print("----------------------------------------------------------------------------")
# === Print DUT info ===
print(f"DUT Name        : {config.get('dut_name')}")
print(f"Num Interfaces  : {config.get('num_interfaces')}")

# === Print each interface ===
print("\nParsed Interface Configurations:")
for i, intf in enumerate(config.get("interfaces", []), start=1):
    print(f"[{i}] Name: {intf.get('name')}, Mode: {intf.get('mode')}, Speed: {intf.get('speed')}, "
          f"Clk: {intf.get('clk')}, Rst: {intf.get('rst')}, Rst Type: {intf.get('rst_type')}")
print("----------------------------------------------------------------------------")

#  creating directory structure as 
#  <your current PWD>/verif/
#  ├── TOP/
#  ├── TEST_LIB/
#  ├── SEQ_LIB/
#  ├── ENV/
#  │   ├── AGENTS/
#  │   └── SBD/
#  ├── RAL/

def create_uvm_tb_dirs():
    # Get current working directory
    base_dir = os.getcwd()

    # Base verification directory
    verif_dir = os.path.join(base_dir, "verif")

    # Define all required subdirectories
    dirs_to_create = [
        os.path.join(verif_dir, "TOP"),
        os.path.join(verif_dir, "TEST_LIB"),
        os.path.join(verif_dir, "SEQ_LIB"),
        os.path.join(verif_dir, "ENV"),
        os.path.join(verif_dir, "ENV", "AGENTS"),
        os.path.join(verif_dir, "ENV", "SBD"),
        os.path.join(verif_dir, "RAL"),
        os.path.join(verif_dir, "SIM")
    ]

    # Create directories
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        print(f"Created: {d}")

create_uvm_tb_dirs()
print("----------------------------------------------------------------------------")

# generate rst logic based on rst_type
# Active-High Reset (rst_type == "1"):
# rst = 1; @(posedge clk); rst = 0;
# Active-Low Reset (rst_type == "0"):
# rst = 0; @(posedge clk); rst = 1;

def generate_top_sv_from_cfg(config):
    top_sv_path = os.path.join(os.getcwd(), "verif", "TOP", "top.sv")
    lines = []

    lines.append("module top;\n")

    # === Signal Declarations ===
    for intf in config.get("interfaces", []):
        clk = intf.get("clk")
        rst = intf.get("rst")

        if clk and clk.lower() != "nil":
            lines.append(f"  logic {clk};")
        if rst and rst.lower() != "nil":
            lines.append(f"  logic {rst};")
    lines.append("")

    # === Clock Generators ===
    for intf in config.get("interfaces", []):
        clk = intf.get("clk")
        speed = intf.get("speed")

        if not clk or clk.lower() == "nil" or not speed or speed.lower() == "nil":
            continue

        try:
            speed = int(speed)
            if speed <= 0:
                continue
            period_ns = round(1000 / speed, 3)
            half_period = round(period_ns / 2, 3)

            lines.append(f"  // {clk} clock generation at {speed} MHz (~{period_ns}ns)")
            lines.append(f"  initial {clk} = 0;")
            lines.append(f"  always #{half_period} {clk} = ~{clk};\n")
        except (ValueError, ZeroDivisionError):
            continue

    # === Reset Pulses Using @(posedge clk) ===
    for intf in config.get("interfaces", []):
        clk = intf.get("clk")
        rst = intf.get("rst")
        rst_type = intf.get("rst_type")

        if not clk or clk.lower() == "nil":
            continue
        if not rst or rst.lower() == "nil":
            continue
        if not rst_type:
            continue

        active_high = rst_type == "1"
        assert_val = "1" if active_high else "0"
        deassert_val = "0" if active_high else "1"

        lines.append(f"  // {rst} reset pulse using @{clk}, active {'high' if active_high else 'low'}")
        lines.append("  initial begin")
        lines.append(f"    {rst} = {assert_val};")
        lines.append(f"    @(posedge {clk});")
        lines.append(f"    {rst} = {deassert_val};")
        lines.append("  end\n")

    # === Interface Instantiations ===
    lines.append("  // Interface Instantiations")
    for intf in config.get("interfaces", []):
        name = intf.get("name")
        if name and name.lower() != "nil":
            inst_name = name.lower() + "_pif"
            lines.append(f"  {name.lower()}_if {inst_name}();  // TODO: Create {name} interface files")
    lines.append("")

	 # === DUT Instantiation ===
    dut_name = config.get("dut_name", "dut")
    lines.append(f"  // DUT instantiation")
    lines.append(f"  {dut_name} u_{dut_name.lower()} (")
    lines.append("    // TODO: Connect ports using pif handles ")
    lines.append("  );\n")

    # === UVM Run Test with lowercase DUT-based name ===
    dut_name = config.get("dut_name", "dut")
    test_name = f"{dut_name.lower()}_base_test"
    lines.append("  // UVM run_test() call")
    lines.append("  initial begin")
    lines.append(f"    run_test(\"{test_name}\");")
    lines.append("  end\n")

    # === Pass Interfaces to UVM via uvm_config_db ===
    lines.append("  // Passing interfaces to UVM via uvm_config_db")
    lines.append("  initial begin")
    for intf in config.get("interfaces", []):
        name = intf.get("name")
        if name and name.lower() != "nil":
            iface_type = f"{name.lower()}_if"
            inst_name = f"{name.lower()}_pif"
            lines.append(f"    uvm_config_db#(virtual {iface_type})::set(null, \"*\", \"vif\", {inst_name});")
    lines.append("  end\n")


    lines.append("endmodule")

    with open(top_sv_path, "w") as f:
        f.write("\n".join(lines))
        print(f"Generated: {top_sv_path}\n")

    # === Prepare README Summary ===
    readme_lines = []
    intfs = config.get("interfaces", [])
	 
    readme_lines.append("top.sv generation summary\n")
    readme_lines.append(f"DUT Name             : {dut_name}")
    readme_lines.append(f"Number of Interfaces : {config.get('num_interfaces')}\n")

    readme_lines.append("top.sv contents:")
    readme_lines.append(f"- `module top;` with DUT `{dut_name}` instantiated")

    if any(intf.get("clk") for intf in intfs):
        readme_lines.append("- Clock signal declarations and generation:")
        for intf in intfs:
            clk = intf.get("clk")
            speed = intf.get("speed")
            if clk and clk.lower() != "nil":
                speed_str = f"{speed} MHz" if speed else "default"
                readme_lines.append(f"    • {clk}  ({speed_str})")

    if any(intf.get("rst") for intf in intfs):
        readme_lines.append("- Reset pulse logic based on @posedge clk:")
        for intf in intfs:
            rst = intf.get("rst")
            clk = intf.get("clk")
            rst_type = intf.get("rst_type")
            if rst and clk:
                type_str = "active high" if rst_type == "1" else "active low" if rst_type == "0" else "unspecified"
                readme_lines.append(f"    • {rst}  ({type_str}) driven by {clk}")

    readme_lines.append("- Interface instantiations:")
    for intf in intfs:
        name = intf.get("name")
        if name:
            readme_lines.append(f"    • {name.lower()}_if {name.lower()}_if_inst();")

    readme_lines.append("- uvm_config_db set() calls to pass virtual interfaces")
    readme_lines.append(f"- run_test(\"{dut_name.lower()}_base_test\")` to launch simulation\n")

    readme_lines.append("TODOs for User To code in top.sv:")
    readme_lines.append("- Connect interface instances to DUT ports:")
    for intf in intfs:
        name = intf.get("name")
        if name:
            readme_lines.append(f"    • Connect `{name.lower()}_if_inst` to DUT")
    readme_lines.append("- Define SystemVerilog interface files (*.sv)")
    readme_lines.append("\n-----------------------------------------------------------")

    sim_dir = os.path.join(os.getcwd(), "verif", "SIM")
    os.makedirs(sim_dir, exist_ok=True)
    
    readme_path = os.path.join(sim_dir, "README.txt")
	 
    with open(readme_path, "w") as readme_file:
        readme_file.write("\n".join(readme_lines))
        print("Refer to README.txt for a detailed summary of top.sv file:")
        print(f"   → {readme_path}")

    print("----------------------------------------------------------------------------")

generate_top_sv_from_cfg(config)

def generate_uvm_test(config):
    """
    Generate a UVM base test class file named <dut_name>_base_test.sv
    under the directory verif/TEST_LIB/.
    """
    dut_name = config.get("dut_name", "").strip().lower()
    if not dut_name:
        print("No DUT name found in configuration. Skipping UVM test generation.")
        return

    # Construct names
    test_class = f"{dut_name}_base_test"
    env_class = f"{dut_name}_env"
    seq_class = f"{dut_name}_base_seq"

    # Create TEST_LIB directory if needed
    test_dir = os.path.join(os.getcwd(), "verif", "TEST_LIB")
    sim_dir = os.path.join(os.getcwd(), "verif", "SIM")
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(sim_dir, exist_ok=True)
    test_file_path = os.path.join(test_dir, f"{test_class}.sv")
    readme_path = os.path.join(sim_dir, "README.txt")
	 

    # === Generate file content without leading spaces ===
    content = textwrap.dedent(f"""\
	 // ----------------------------------------------------
	 // UVM Test: {test_class}
	 // ----------------------------------------------------
	 class {test_class} extends uvm_test;
	   `uvm_component_utils({test_class})
	 
	   // Environment handle
	   {env_class} {env_class}_h;
	 
	   function new(string name = "{test_class}", uvm_component parent = null);
	     super.new(name, parent);
	   endfunction
	 
	   virtual function void build_phase(uvm_phase phase);
	     super.build_phase(phase);
	  	{env_class}_h = {env_class}::type_id::create("{env_class}_h", this);
	   endfunction
	 
	   virtual task run_phase(uvm_phase phase);
	     {seq_class} seq = {seq_class}::type_id::create("seq");
		  `uvm_info(get_full_name(),"Run_phase started", UVM_NONE)
	 
	     phase.raise_objection(this);
	 
	     // TODO: Update sequencer path if not {env_class}_h.sqr
	     seq.start({env_class}_h.sqr);
	 
	  	phase.phase_done.set_drain_time(this,1000);
	  	phase.drop_objection(this);

	  	`uvm_info(get_full_name(),"Run_phase End", UVM_NONE)
	 
	   endtask
	 
	 endclass : {test_class}
    """)

    # Write file
    with open(test_file_path, "w") as f:
        f.write(content)

    print(f"Generated: {test_file_path}")

	# Append summary to README.txt
    summary = textwrap.dedent(f"""\
        

        {test_class}.sv Summary

        Class Structure:
        - class {test_class} extends uvm_test
        - Factory registered using `uvm_component_utils({test_class})`
        - build_phase(): creates `{env_class}`
        - run_phase():
            - Creates `{seq_class}`
            - Raises/drops uvm_objection
            - Calls `start()` on `{env_class}_h.sqr`
        ------------------------------------------------------------------------
		""")
    with open(readme_path, "a") as rf:
        rf.write(summary)
        print("\nRefer to README.txt for a detailed summary of top.sv file:")
        print(f"   → {readme_path}")

    print("----------------------------------------------------------------------------")

generate_uvm_test(config)


def generate_uvm_env(config):
    """
    Generates <dut_name>_env.sv inside verif/ENV/
    and appends a summary to verif/SIM/README.txt.
    """
    dut_name = config.get("dut_name", "").strip().lower()
    interfaces = config.get("interfaces", [])
    if not dut_name:
        print("No DUT name provided. Cannot generate env.")
        return

    env_class = f"{dut_name}_env"

    agent_inst_block = ""
    create_agent_block = ""
    
    sbd_class_name = f"{dut_name}_sbd"
    sbd_class_inst_name = f"{sbd_class_name}_h"
    sbd_inst = f"{sbd_class_name} {sbd_class_inst_name}"
    create_sbd = f'{sbd_class_inst_name} = {sbd_class_name}::type_id::create("{sbd_class_inst_name}", this);'

    env_dir = os.path.join(os.getcwd(), "verif", "ENV")
    os.makedirs(env_dir, exist_ok=True)
    env_file_path = os.path.join(env_dir, f"{env_class}.sv")

    with open(env_file_path, "w") as f:
    		f.write(f"// ----------------------------------------------------\n")
    		f.write(f"// UVM Environment: {env_class}\n")
    		f.write(f"// ----------------------------------------------------\n")
    		f.write(f"class {env_class} extends uvm_env;\n")
    		f.write(f"	`uvm_component_utils({env_class})\n")

    		# Agents
    		f.write(f"\n	//Agents instantiation\n")
    		for intf in interfaces:
    		    name = intf.get("name", "if").lower()
    		    agent_class = f"{name}_agent"
    		    inst = f"{agent_class}_h"
    		    f.write(f"	{agent_class} {inst};\n")

    		# Scoreboard
    		f.write(f"\n	//Scoreboard instantiation\n")
    		f.write(f"	//{sbd_inst};\n\n")

    		# Constructor
    		f.write(f"	function new(string name = \"{env_class}\", uvm_component parent = null);\n")
    		f.write(f"		super.new(name, parent);\n")
    		f.write("	endfunction\n\n")

    		# Build phase
    		f.write("	virtual function void build_phase(uvm_phase phase);\n")
    		f.write("		super.build_phase(phase);\n")
    		for intf in interfaces:
    		    name = intf.get("name", "if").lower()
    		    agent_class = f"{name}_agent"
    		    inst = f"{agent_class}_h"
    		    f.write(f'		{inst} = {agent_class}::type_id::create("{inst}", this);\n')
    		f.write(f'		//{sbd_class_inst_name} = {sbd_class_name}::type_id::create("{sbd_class_inst_name}", this);\n')
    		f.write("	endfunction\n\n")

			# connect_phase phase
    		f.write("	virtual function void connect_phase(uvm_phase phase);\n")
    		for intf in interfaces:
    		    name = intf.get("name", "if").lower()
    		    agent_class = f"{name}_agent"
    		    inst = f"{agent_class}_h"
    		    f.write(f'  		//TODO - Check the SBD connection\n')
    		    f.write(f'		//{inst}.{name}_h.{name}_ap_h.connect({sbd_class_inst_name}.analysis_export);\n')
    		f.write("	endfunction\n\n")

    		f.write(f"endclass : {env_class}\n")


    print(f"Generated : {env_file_path}")

    sim_dir = os.path.join(os.getcwd(), "verif", "SIM")
    os.makedirs(sim_dir, exist_ok=True)

    readme_path = os.path.join(sim_dir, "README.txt")


    # === Append Summary to README.txt ===
    summary = textwrap.dedent(f"""\
        
 {env_class}.sv Summary

 Class Structure:
 - class {env_class} extends uvm_env
 - Factory registration using `uvm_component_utils`
 - One agent per interface: {[intf.get('name', 'IF') for intf in interfaces]}
 - One scoreboard instance: sbd
 - User need to Implement SBD file manually as of now. Script might be modified in future for SBD generation.

 Instantiated Components:
{chr(10).join([f"        - {intf.get('name', 'if').lower()}_agent ({intf.get('name', '').upper()} protocol)" for intf in interfaces])}
 - m_sbd : scoreboard

 TODOs for User:
 - check the agent to SBD connection
 ------------------------------------------------------------------------
    """)

    with open(readme_path, "a") as rf:
        rf.write(summary)
        print("\nRefer to README.txt for a detailed summary of top.sv file:")
        print(f"   → {readme_path}")

    print("----------------------------------------------------------------------------")

generate_uvm_env(config)

def create_full_agent_and_components(cfg):
    """
    Generates agent class and its components using f.write()
    - agent_class.sv
    - *_drv.sv, *_sqr.sv (if M), *_mon.sv, *_cov.sv (if M/S)
    - Appends summary to README.txt
    """

    interfaces = cfg.get("interfaces", [])
    agents_dir = os.path.join(os.getcwd(), "verif", "ENV", "AGENTS")
    sim_dir = os.path.join(os.getcwd(), "verif", "SIM")
    os.makedirs(agents_dir, exist_ok=True)
    os.makedirs(sim_dir, exist_ok=True)

    readme_path = os.path.join(sim_dir, "README.txt")
    with open(readme_path, "a") as readme:
        readme.write("\n\nAgent & Component Summary\n")

        for intf in interfaces:
            name = intf.get("name", "").strip().lower()
            drv_name = f"{name}_drv";
            drv_inst = f"{drv_name}_h";

            sqr_name = f"{name}_sqr";
            sqr_inst = f"{sqr_name}_h";

            mon_name = f"{name}_mon";
            mon_inst = f"{mon_name}_h";

            cov_name = f"{name}_cov";
            cov_inst = f"{cov_name}_h";
				
            mode = intf.get("mode", "").strip().upper()
            if not name or mode not in ["M", "S"]:
                continue

            agent_class = f"{name}_agent"
            agent_dir = os.path.join(agents_dir, name)
            os.makedirs(agent_dir, exist_ok=True)
            agent_file = os.path.join(agent_dir, f"{agent_class}.sv")

            # === Write Agent Class ===
            with open(agent_file, "w") as f:
                f.write(f"// ----------------------------------------------------\n")
                f.write(f"//UVM agent: {agent_class}\n")
                f.write(f"//----------------------------------------------------\n")
                f.write(f"class {agent_class} extends uvm_agent;\n")
                f.write(f"`uvm_component_utils({agent_class})\n\n")

                f.write(f"//Sub-Component Instantiation\n")
                if mode == "M":
                    f.write(f"{drv_name} {drv_inst};\n")
                    f.write(f"{sqr_name} {sqr_inst};\n")
                f.write(f"{mon_name} {mon_inst};\n")
                f.write(f"{cov_name} {cov_inst};\n\n")

                f.write(f"function new(string name = \"{agent_class}\", uvm_component parent = null);\n")
                f.write(f"  super.new(name, parent);\n")
                f.write(f"endfunction\n\n")

                f.write(f"virtual function void build_phase(uvm_phase phase);\n")
                f.write(f"  super.build_phase(phase);\n")
                f.write(f"  {mon_inst} = {mon_name}::type_id::create(\"{mon_inst}\", this);\n")
                f.write(f"  {cov_inst} = {cov_name}::type_id::create(\"{cov_inst}\", this);\n")
                if mode == "M":
                    f.write(f"  {drv_inst} = {drv_name}::type_id::create(\"{drv_inst}\", this);\n")
                    f.write(f"  {sqr_inst} = {sqr_name}::type_id::create(\"{sqr_inst}\", this);\n")
                f.write(f"endfunction\n\n")

                f.write(f"virtual function void connect_phase(uvm_phase phase);\n")
                f.write(f"  super.connect_phase(phase);\n")
                if mode == "M":
                    f.write(f"  {drv_inst}.seq_item_port.connect({sqr_inst}.seq_item_export);\n")
                f.write(f"  {mon_inst}.{name}_ap_h.connect({cov_inst}.analysis_export);\n")
                f.write(f"endfunction\n\n")
                
                f.write(f"endclass : {agent_class}\n")

            print(f"Created agent class: {agent_file}")
            readme.write(f" -{agent_class}.sv\n")

            # === Component Classes ===
            components = {"mon": "uvm_monitor", "cov": "uvm_subscriber"}
            if mode == "M":
                components.update({"drv": "uvm_driver", "sqr": "uvm_sequencer"})

            for suffix, base_class in components.items():
                class_name = f"{name}_{suffix}"
                comp_file = os.path.join(agent_dir, f"{class_name}.sv")
                with open(comp_file, "w") as cf:
                    cf.write(f"// ----------------------------------------------------\n")
                    cf.write(f"//UVM {suffix}: {class_name}\n")
                    cf.write(f"//----------------------------------------------------\n")
                    if suffix == "sqr":
                        cf.write(f"typedef {base_class}#({name}_tx) {class_name};")
                    else:
                        if suffix == "drv":
                           cf.write(f"class {class_name} extends {base_class}#({name}_tx);\n")
                           cf.write(f"`uvm_component_utils({class_name})\n\n")
                           cf.write(f'virtual {name}_if {name}_vif;\n\n')

                           cf.write(f"function new(string name = \"{class_name}\", uvm_component parent = null);\n")
                           cf.write(f"  super.new(name, parent);\n")
                           cf.write(f"endfunction : new\n\n")

                           cf.write(f'virtual function void build_phase(uvm_phase phase);\n')
                           cf.write(f'  super.build_phase(phase);\n')
                           cf.write(f'  if(!uvm_config_db#(virtual {name}_if)::get(this,"","vif",{name}_vif))\n')
                           cf.write(f'     `uvm_error(get_full_name(),"FAILED TO RETRIVE VIF HANDLE FROM CONFIG_DB")\n')
                           cf.write(f"endfunction : build_phase\n\n")
                           
                           cf.write(f'virtual task run_phase(uvm_phase phase);\n')
                           cf.write(f'`uvm_info(get_full_name(),"run_phase START",UVM_NONE)\n')
                           cf.write(f'  forever begin\n')
                           cf.write(f'    seq_item_port.get_next_item(req);\n')
                           cf.write(f'    //req.print();\n')
                           cf.write(f'    drive_tx(req);\n')
                           cf.write(f'    seq_item_port.item_done();\n')
                           cf.write(f'  end\n')
                           cf.write(f'endtask : run_phase\n\n')

                           cf.write(f'task drive_tx({name}_tx tx);\n')
                           cf.write(f"  // TODO: Implement {name} specific drive logic functionality\n")
                           cf.write(f'endtask : drive_tx\n\n')

                        if suffix == "mon":
                           cf.write(f"class {class_name} extends {base_class};\n")
                           cf.write(f"`uvm_component_utils({class_name})\n\n")
                           cf.write(f'virtual {name}_if {name}_vif;\n\n')
                           cf.write(f'uvm_analysis_port#({name}_tx) {name}_ap_h;\n\n')
                           cf.write(f'{name}_tx tx;\n\n')
                           
                           cf.write(f"function new(string name = \"{class_name}\", uvm_component parent = null);\n")
                           cf.write(f"  super.new(name, parent);\n")
                           cf.write(f"endfunction : new\n\n")
                           
                           cf.write(f'virtual function void build_phase(uvm_phase phase);\n')
                           cf.write(f'  super.build_phase(phase);\n')
                           cf.write(f'  tx = {name}_tx::type_id::create("tx");\n')
                           cf.write(f'  {name}_ap_h = new("{name}_ap_h",this);\n')
                           cf.write(f'  if(!uvm_config_db#(virtual {name}_if)::get(this,"","vif",{name}_vif))\n')
                           cf.write(f'     `uvm_error(get_full_name(),"FAILED TO RETRIVE VIF HANDLE FROM CONFIG_DB")\n')
                           cf.write(f"endfunction : build_phase\n\n")
									
                           cf.write(f'virtual task run_phase(uvm_phase phase);\n')
                           cf.write(f'`uvm_info(get_full_name(),"run_phase START",UVM_NONE)\n')
                           cf.write(f'  forever begin\n')
                           cf.write(f'    //TODO: Implement {name} specific mon logic functionality\n')
                           cf.write(f'    {name}_ap_h.write(tx);\n')
                           cf.write(f'  end\n')
                           cf.write(f'endtask : run_phase\n\n')
								
                        if suffix == "cov":
                           cf.write(f"class {class_name} extends {base_class}#({name}_tx);\n")
                           cf.write(f"`uvm_component_utils({class_name})\n\n")
                           cf.write(f'{name}_tx tx;\n\n')
                           
                           cf.write(f"covergroup cg;\n")
                           cf.write(f"  //TODO - Implement protocol specific FC\n\n")
                           cf.write(f"endgroup\n\n")
                        
                           cf.write(f"function new(string name = \"{class_name}\", uvm_component parent = null);\n")
                           cf.write(f"  super.new(name, parent);\n")
                           cf.write(f"  cg = new();\n")
                           cf.write(f"endfunction : new\n\n")
                        
                           cf.write(f'virtual function void write(T t);\n')
                           cf.write(f'  $cast(tx,t);\n')
                           cf.write(f'  cg.sample();\n')
                           cf.write(f'endfunction : write\n\n')
                           
                        cf.write(f"endclass : {class_name}\n")

                print(f"Created component: {comp_file}")
                readme.write(f"   └── {class_name}.sv (extends {base_class})\n")

    with open(readme_path, "a") as rf:
          rf.write(f'TODO for User:\n')
          rf.write(f'- In Driver file\n')
          rf.write(f'-- Implement Protocol specific drive logic functionality\n')
          rf.write(f'- In Cov file\n')
          rf.write(f'-- Implement protocol specific FC\n')
          rf.write(f'- In Mon file\n')
          rf.write(f'-- Implement protocol specific mon logic functionality\n')
          rf.write(f'---------------------------------------------------------------------------\n')
          
          print("\nRefer to README.txt for a detailed summary of agents and its components file:")
          print(f"   → {readme_path}")

    print("----------------------------------------------------------------------------")

create_full_agent_and_components(config)

def generate_base_seq(cfg):
    """
    Generates <dut_name>_base_seq.sv inside verif/SEQ_LIB/
    - Class extends uvm_sequence
    - Factory registration
    - new() constructor
    - body() with `uvm_info` and `uvm_do_with`
    """

    dut_name = cfg.get("dut_name", "").strip().lower()
    if not dut_name:
        print("No DUT name found in config. Skipping base sequence generation.")
        return

    seq_class = f"{dut_name}_base_seq"
    seq_dir = os.path.join(os.getcwd(), "verif", "SEQ_LIB")
    sim_dir = os.path.join(os.getcwd(), "verif", "SIM")
    os.makedirs(seq_dir, exist_ok=True)
    os.makedirs(sim_dir, exist_ok=True)

    seq_file = os.path.join(seq_dir, f"{seq_class}.sv")
    readme_path = os.path.join(sim_dir, "README.txt")

    with open(seq_file, "w") as f:
        f.write(f"// ----------------------------------------------------\n")
        f.write(f"//UVM sequence: {seq_class}\n")
        f.write(f"//----------------------------------------------------\n")
        f.write(f"class {seq_class} extends uvm_sequence;\n")
        f.write(f"`uvm_object_utils({seq_class})\n\n")

        f.write(f"function new(string name = \"{seq_class}\");\n")
        f.write( "  super.new(name);\n")
        f.write( "endfunction\n\n")

        f.write( "virtual task body();\n")
        f.write(f"  `uvm_info(get_type_name(), \"Starting {seq_class}\", UVM_NONE)\n")
        f.write(f"  //Randomizing req\n")
        f.write(f"  `uvm_do(req)\n")
        f.write( "endtask\n\n")

        f.write(f"endclass : {seq_class}\n")

    print(f"Generated base sequence: {seq_file}")

    # === Append summary to README.txt ===
    with open(readme_path, "a") as rf:
        rf.write(f"""\n{seq_class}.sv Summary
- Class {seq_class} extends uvm_sequence
- Factory registration with `uvm_object_utils`
- new() constructor
- body() includes:
   - `uvm_info` to indicate start of sequence
   - `uvm_do macro which allows tool to randomize the tx fields
- TODO: Define sequence item type (req) and if needed use uuvm_do_with instead of uvm_do
---------------------------------------------------------------------------------------------
""")

    print("\nRefer to README.txt for a detailed summary of agents and its components file:")
    print(f"   → {readme_path}")


    print("----------------------------------------------------------------------------")

generate_base_seq(config)

log_file.close()  # only needed if using direct open/write

