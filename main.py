from Schedule import Schedule
from datetime import datetime


if __name__ == "__main__":
    start_time = datetime.now()

    schedule = Schedule("schema.txt", ["TE", "EE", "ES"], "P1")
    schedule.run_schedule_operations()

    end_time = datetime.now()
    print(f"Time taken with multiprocessing: {end_time - start_time}")