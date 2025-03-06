# trackshape-utils

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-%20%20GNU%20GPL%20v3%20-blue)

Collection of utilities to modify existing MSTS/ORTS track shapes


## Installation

Install using `pip`:

```sh
pip install my_package
```

Or install from source:

```sh
git clone https://github.com/yourusername/my_package.git
cd my_package
pip install .
```


## Usage

Import and use the package in your Python code:

```python
import trackshapeutils as tsu

result = tsu.some_function()
print(result)
```


## Running Tests

We use `pytest` for testing. You can run tests manually or use `tox` to test across multiple Python versions.

### Run Tests Manually
First, install the required dependencies:

```sh
pip install pytest
```

Then, run tests with:

```sh
pytest
```


## Run Tests with `tox`

`tox` allows you to test across multiple Python environments.

### **1. Install `tox`**
```sh
pip install tox
```

### **2. Run Tests**
```sh
tox
```

This will execute tests in all specified Python versions.

### **3. `tox.ini` Configuration**
The `tox.ini` file should be in your project root:

```ini
[tox]
envlist = py38, py39, py310

[testenv]
deps = pytest
commands = pytest
```

Modify `envlist` to match the Python versions you want to support.


## License

This project is licensed under the GNU GPL v3 - see the [LICENSE](LICENSE) file for details.
