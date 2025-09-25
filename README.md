# Qwen3-Next-Thinking Model Test Script Documentation

## Overview

The `test_qwen_thinking_235b.sh` script is a comprehensive testing framework designed to evaluate the Qwen3-Next-Thinking model (qwen3-235b-thinking) using the AgentSafe evaluation system. This script provides automated testing capabilities with configurable parameters for different test levels, difficulties, and execution modes.

## Features

- **Automated Model Testing**: Streamlined testing process for the Qwen3-235b-thinking model
- **Configurable Test Parameters**: Support for different test levels, difficulties, and test counts
- **Resume Functionality**: Ability to resume from existing test trajectories
- **API Health Checks**: Automatic verification of API connectivity before testing
- **Colored Output**: Enhanced terminal output with color-coded status messages
- **Error Handling**: Robust error handling with proper exit codes
- **Dependency Validation**: Pre-flight checks for required files and dependencies

## Prerequisites

### System Requirements
- **Operating System**: Unix-like system (Linux, macOS)
- **Shell**: Bash shell environment
- **Python**: Python 3.x installed and accessible via `python3` command
- **Network**: Internet connectivity for API access
- **Tools**: `curl` command available for API testing

### Required Files
- `run_simple_test.py`: Main Python test runner script
- `merged_tasks_updated.jsonl`: Test dataset file
- Valid API credentials and endpoint access

## Configuration

### Model Configuration
```bash
MODEL_NAME="qwen3-235b-thinking"
API_KEY="none"
API_URL=""
BASE_OUTPUT_DIR=""
DATASET=""
```

### Test Parameters
- **MAX_ITERATIONS**: 30 (Maximum iterations per test)
- **TEMPERATURE**: 0.6 (Model temperature setting)
- **TIMEOUT**: 600 seconds (Test timeout)
- **MAX_WORKERS**: 2 (Parallel execution workers)

## Usage

### Basic Syntax
```bash
./test_qwen_thinking_235b.sh [TEST_LEVEL] [TEST_DIFFICULTY] [MAX_TESTS]
```

### Parameters

#### TEST_LEVEL (Optional, Default: "All")
Specifies the test level to execute:
- `All`: Run all test levels
- `0`, `1`, `2`, `3`: Run specific test level
- `[0,2]`: Run multiple specific levels (L0 and L2)

#### TEST_DIFFICULTY (Optional, Default: "All")
Specifies the test difficulty:
- `All`: Run all difficulty levels
- `Low`: Run only low difficulty tests
- `Medium`: Run only medium difficulty tests
- `High`: Run only high difficulty tests
- `[Low,High]`: Run multiple specific difficulties

#### MAX_TESTS (Optional, Default: "all")
Limits the number of tests to execute:
- `all`: Run all available tests
- `<number>`: Run specified number of tests (e.g., `10`, `50`)

### Usage Examples

#### Run All Tests
```bash
./test_qwen_thinking_235b.sh
```

#### Run Specific Level and Difficulty
```bash
./test_qwen_thinking_235b.sh 0 Low
```

#### Run Limited Number of Tests
```bash
./test_qwen_thinking_235b.sh All All 10
```

#### Run Multiple Levels with All Difficulties
```bash
./test_qwen_thinking_235b.sh [0,2] All
```

#### Get Help Information
```bash
./test_qwen_thinking_235b.sh --help
# or
./test_qwen_thinking_235b.sh -h
```

## Script Workflow

### 1. Initialization
- Parse command-line arguments
- Set default values for unspecified parameters
- Display configuration information

### 2. Dependency Validation
- Check Python 3 availability
- Verify existence of `run_simple_test.py`
- Validate dataset file presence

### 3. Environment Setup
- Create output directory structure
- Test API connectivity
- Set required environment variables

### 4. Resume Detection
- Check for existing trajectory directories
- Automatically detect resumable test sessions
- Configure resume parameters if applicable

### 5. Test Execution
- Build command arguments array
- Execute the Python test runner
- Monitor execution progress

### 6. Results Reporting
- Display execution summary
- Report success/failure status
- Provide output directory information

## Output Structure

### Directory Layout
```

├── {TEST_LEVEL}_{TEST_DIFFICULTY}/
│   ├── trajectories/
│   │   └── *qwen3-235b-thinking*/
│   └── reports/
```

