# Code Execution Engine Fix

## Problem
The screening coding challenges (Min-Max Normalization, Remove Outliers) were failing with:
> ⚠ Code execution engine not available

## Root Cause
Missing dependencies in the Python environment:
- `RestrictedPython` - optional, but preferred for sandboxed code execution
- `numpy` - required for data science coding challenges

## Solution

### Step 1: Install Missing Dependencies
```bash
# Option 1: Install all at once
pip install -r requirements.txt

# Option 2: Install specific packages
pip install numpy RestrictedPython
```

### Step 2: Verify Installation
```bash
# Check if numpy is available
python3 -c "import numpy; print(f'✅ NumPy {numpy.__version__}')"

# Check if RestrictedPython is available
python3 -c "import restricted_python; print('✅ RestrictedPython available')"

# Or check both
pip list | grep -E "numpy|RestrictedPython"
```

### Step 3: Restart the Flask App
```bash
python app.py
```

### Step 4: Test the Fixed Code Execution
1. Go to `http://127.0.0.1:5000`
2. Start the screening test
3. Try the data analyst questions:
   - **Min-Max Normalization** - should now execute
   - **Remove Outliers** - should now execute

---

## How It Works Now

The improved code execution engine (in `screening_routes.py`) now:

### Flow
```
1. Try RestrictedPython (preferred - safer sandboxing)
   ✓ If available → execute code securely
   
2. Fall back to simple exec (if RestrictedPython missing)
   ✓ Supports numpy/pandas imports
   ✓ Whitelist of safe builtins
   
3. Execute test cases against user code
   ✓ Run each test input
   ✓ Compare outputs
   ✓ Handle floating point precision (within 1e-6)
```

### Example: Min-Max Normalization

**User code:**
```python
def min_max_normalize(data):
    min_val = min(data)
    max_val = max(data)
    return [(x - min_val) / (max_val - min_val) for x in data]
```

**What happens:**
1. ✅ Code gets executed
2. ✅ Function is extracted from namespace
3. ✅ Test cases run:
   - Test 1: `[1, 2, 3]` → Expected: `[0.0, 0.5, 1.0]`
   - Test 2: `[10, 20]` → Expected: `[0.0, 1.0]`
   - Test 3: `[5]` → Expected: `[0.0]` (single value edge case)
4. ✅ Results returned to user

---

## Supported Builtins for Code Execution

### Always Available
- `len`, `range`, `zip`, `enumerate`
- `list`, `dict`, `set`, `tuple`
- `int`, `str`, `float`, `bool`
- `min`, `max`, `sum`, `abs`, `round`
- `any`, `all`, `sorted`, `isinstance`

### Available if Installed
- `numpy` (as `np`)
- `pandas` (as `pd`)

### Examples of Working Code

✅ **Basic Data Operations**
```python
def find_average(nums):
    return sum(nums) / len(nums) if nums else 0.0
```

✅ **With NumPy** (after pip install numpy)
```python
def find_average(nums):
    import numpy
    return float(numpy.mean(nums)) if nums else 0.0
```

✅ **With Pandas**
```python
def process_data(df_dict):
    import pandas
    df = pandas.DataFrame(df_dict)
    return df.sum().tolist()
```

❌ **Not Allowed** (security restrictions)
```python
import os  # ❌ Can't access OS
open('/etc/passwd')  # ❌ Can't access files
__import__('subprocess')  # ❌ Can't run commands
eval('1+1')  # ❌ Eval/exec not in whitelist
```

---

## Troubleshooting

### Still seeing "Code execution engine not available"?

1. **Check RestrictedPython is installed:**
   ```bash
   pip install RestrictedPython
   ```

2. **Restart Flask app:**
   ```bash
   # Kill the running app (Ctrl+C)
   # Then restart
   python app.py
   ```

3. **Check Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

4. **Check imports in terminal:**
   ```bash
   python3 << 'EOF'
   try:
       import numpy
       print("✅ numpy OK")
   except:
       print("❌ numpy missing - run: pip install numpy")
   
   try:
       import restricted_python
       print("✅ RestrictedPython OK")
   except:
       print("❌ RestrictedPython missing - run: pip install RestrictedPython")
   EOF
   ```

### Code runs but tests fail?

1. **Check test case format:**
   - Input should be a tuple/list: `{"input": ([1, 2, 3],)}`
   - Expected should match output type

2. **Check floating point comparison:**
   - Lists of floats compared within 1e-6 tolerance
   - Useful for normalization and ML preprocessing

3. **Check output type:**
   - If test expects list, return list
   - If test expects float, return float
   - Don't mix types

---

## Performance Notes

### Execution Limits
- No timeout currently enforced
- For production, add timeout wrapper:
  ```python
  from signal import signal, SIGALRM
  def timeout_handler(signum, frame):
      raise TimeoutError("Code execution exceeded time limit")
  signal(SIGALRM, timeout_handler)
  signal(SIGALRM, 5)  # 5 second timeout
  ```

### Memory Limits
- No memory limits enforced
- For production, use containerized execution (Docker, AWS Lambda, etc.)

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Restart Flask app
3. ✅ Test coding challenges
4. 📊 Monitor performance
5. 🔐 For production: use sandboxed container execution

Ready to test? Run:
```bash
pip install -r requirements.txt && python app.py
```
