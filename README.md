# UVM_TB_GEN_PY_SCRIPT

A Python-based utility to auto-generate **UVM Testbench (TB) skeletons** in UVM from a simple CSV configuration file.  
This helps in bootstrapping UVM environments quickly with minimal manual setup.

---

## 📂 Repository Contents

- **Makefile**
  - `clean`: removes `Py_log.txt`
  - `all`: removes `Py_log.txt` and generated `verif/` directory

- **UVM_TB_PARAMS.csv**
  - Input configuration file (CSV format)
  - Defines DUT name, number of interfaces, and their attributes

- **UVM_Tb_generator.py**
  - Main Python script that:
    - Parses CSV input
    - Creates UVM testbench directory structure
    - Generates SystemVerilog files (top, env, agents, seq, test, etc.)
    - Writes summaries into `verif/SIM/README.txt`

---

## 📝 CSV Format

| Field      | Description                                                                 |
|------------|-----------------------------------------------------------------------------|
| DUT_NAME   | Name of the DUT                                                             |
| NUM_INTF   | Number of interfaces                                                        |
| INTF       | `<Name>,<Mode>,<Freq>,<ClkName>,[<RstName>,<RstType>]`                      |
|            | - Mode: `M` (Master) / `S` (Slave)                                          |
|            | - Freq: Clock frequency in MHz (e.g., 100)                                  |
|            | - RstType: `active_high` / `active_low`                                     |

### Example
```csv
DUT_NAME     , usb_ctrl
NUM_INTF     , 2
INTF         , i2c , M , 100 , i2c_clk , [i2c_rst , active_low]
INTF         , uart, S , 200 , uart_clk, [uart_rst, active_high]

### Generated Directory Structure
verif/
├── TOP/
│   └── top.sv
├── TEST_LIB/
│   └── <dut>_base_test.sv
├── SEQ_LIB/
│   └── <dut>_base_seq.sv
├── ENV/
│   ├── <dut>_env.sv
│   ├── AGENTS/
│   │   └── <intf>/
│   │       ├── <intf>_agent.sv
│   │       ├── <intf>_drv.sv
│   │       ├── <intf>_sqr.sv
│   │       ├── <intf>_mon.sv
│   │       └── <intf>_cov.sv
│   └── SBD/
├── RAL/
└── SIM/
    └── README.txt   (auto-generated summary of all TB files)

### Usage
1. Edit UVM_TB_PARAMS.csv with your DUT and interface details.
2. Run the Python script:
    python3 UVM_Tb_generator.py
3. Generated files will be placed under verif/.
4. Check verif/SIM/README.txt for a detailed summary of generated files and TODOs.

### Features
1. Auto-generation of:
    top.sv with clock/reset logic, DUT instantiation, and run_test()
    Base test, environment, agents, driver, monitor, sequencer, subscriber, and sequence stubs
2. Directory structure aligned with standard UVM methodology
3. Summary README for quick navigation and TODO tracking
4. Simple, CSV-based configuration — no need to modify Python code for new DUTs

### Limitations
1. RAL model is not generated
2. User must:
    Connect DUT ports to interface instances in top.sv
    Define protocol-specific logic inside driver/monitor/coverage
    Implement Scoreboard (SBD) manually

### License
This project is provided "as is" without warranty.
You are free to modify, distribute, and use it in your own projects.

👤 Author: Koushik Shridhar  
📅 Date: July 06, 2025  
🔖 Version: 1.0.0



