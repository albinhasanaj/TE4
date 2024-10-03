# Schedule Project

## Overview

The Schedule project is designed to manage and process class schedules and pupil information. It leverages Python's powerful libraries such as `pandas` and `multiprocessing` to handle data efficiently.

## Features

- **Class Management**: Dynamically generates class names based on the current year.
- **Pupil Management**: (Feature in progress) Will handle pupil information including their social security numbers.

## Installation

1. Clone the repository:
	```sh
	git clone <repository-url>
	```
2. Navigate to the project directory:
	```sh
	cd <project-directory>
	```
3. Install the required dependencies:
	```sh
	pip install -r requirements.txt
	```

## Usage

1. Import the `Schedule` class from `Schedule.py`:
	```python
	from Schedule import Schedule
	```
2. Initialize the `Schedule` object with the required parameters:
	```python
	schedule = Schedule(data="path/to/data.txt", classes=["ClassA", "ClassB"], period="P1")
	```
3. Use the `get_classes` method to retrieve the list of classes:
	```python
	classes = schedule.get_classes()
	print(classes)
	```

## Dependencies

- `pandas`
- `os`
- `ast`
- `datetime`
- `re`
- `multiprocessing`

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For any questions or suggestions, please open an issue or contact the project maintainer.