import pandas as pd
import os
import ast
from datetime import datetime

def get_classes(classes = ["TE", "EE", "ES"]):
    current_year = datetime.now().year
    current_month = datetime.now().month
    if current_month < 8: # new school year starts in august
        current_year -= 1
        
    current_year = str(current_year)[2:]
    classes = [f"{cls}{year}" for cls in classes for year in range(int(current_year) - 2, int(current_year) + 1)]	
    return classes

def get_pupils_ssn(classes):
    pupils = []
    schema_lines = []
    with open("./schema.txt", "r") as file:
        for line in file:
            schema_lines.append(line.strip())
            for cls in classes:
                if line.startswith(cls):
                    ssns = line.split(",")[1:]
                    pupils.extend([{cls: ssn} for ssn in ssns])
    return pupils, schema_lines


def get_all_lessons(data, schema):
    lessons = []
    schema_dict = {line.split("\t")[0]: line for line in schema}
    for pupil in data:
        for cls, ssn in pupil.items():
            # Get all lessons for the pupil by checking if the SSN is in the schema line and not equal to the class name (SSN != class name)
            pupil_lessons = [{ssn: schema_dict.get(lesson_id).split("\t")[0]} for lesson_id in schema_dict if ssn in schema_dict[lesson_id] and ssn != lesson_id]
            lessons.append({cls: pupil_lessons})
    return lessons

def get_pupil_names(data, schema):
    names = []
    track_row = 0
    for i, line in enumerate(schema):
        if "Student" in line:
            track_row = i
            break
    schema_dict = {line.split("\t")[0]: line for line in schema[track_row:]}
    for pupil in data:
        for cls, ssn in pupil.items():
            if ssn in schema_dict:
                x = [x for x in schema_dict[ssn].split("\t") if x and "{" not in x]
                if len(x) > 2:
                    name = f"{x[1]} {x[2]}"
                    names.append({ssn: name})
    return names

def convert_to_csv(data, names, filename="pupils_lessons.csv"):
    flattened_data = [
        {
            'kurs': cls,
            'personnummer': ssn,
            'lektion': lesson_name,
            'namn': next((name[ssn] for name in names if ssn in name), '')
        }
        for lesson_dict in data for cls, pupil_lessons in lesson_dict.items()
        for lesson in pupil_lessons for ssn, lesson_name in lesson.items() if cls != lesson_name
    ]
    df = pd.DataFrame(flattened_data)
    df.to_csv(filename, index=False)
    return df
    

def add_minutes_to_time(old_time, minutes_to_add):
    """
    Adds a specified number of minutes to a given time in HH:MM format.

    Args:
        old_time (str): The original time in "HH:MM" format.
        minutes_to_add (int): The number of minutes to add to the original time.

    Returns:
        str: The new time in "HH:MM" format.
    """
    old_time_split = old_time.split(":")
    old_time_minutes = int(old_time_split[1])
    old_time_hours = int(old_time_split[0])
    new_time_minutes = old_time_minutes + int(minutes_to_add)

    # Adjust hours and minutes correctly
    new_time_hours = old_time_hours + new_time_minutes // 60
    new_time_minutes = new_time_minutes % 60

    # Format the new time correctly
    return f"{new_time_hours:02}:{new_time_minutes:02}"
    return old_time  # Return the original time if no ":" found
    
    
def format_days_to_lessons(data, df):
    days = ["ndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
    lessons = [
        {
            "Måndag": []
        },
        {
            "Tisdag": []
        },
        {
            "Onsdag": []
        },
        {
            "Torsdag": []
        },
        {
            "Fredag": []
        }
    ]
    for i, line in enumerate(data):
        day_lessons = []
        step = 0
        for day in days:
            if day in line:
                #find the lektion
                for lektion in df["lektion"]:
                    if lektion in line:
                        line_data = line.split("\t")

                        #p2 are lesssons that doesnt make any sense so gone they
                        p2 = False

                        for x in line_data:
                            if x == "P2":
                                p2 = True
                                break

                        if not p2:
                            step = False
                            old_time = ""
                            for x in line_data:

                                if step:
                                    step = False
                                    # append to the lektion: [x+append]
                                    for lesson in lessons:
                                        for key, value in lesson.items():
                                            if key == day:
                                                    if ":" in old_time:
                                                        new_time = add_minutes_to_time(old_time, x)
                                                        value[-1][lektion].append(new_time)
                                                    value[-1][lektion].append(x)
                                                    continue
                                            if key == "Måndag" and day == "ndag":
                                                if ":" in old_time:
                                                    new_time = add_minutes_to_time(old_time, x)
                                                    value[-1][lektion].append(new_time)
                                                value[-1][lektion].append(x)
                                                continue

                                if ":" in x:
                                    step = True
                                    for lesson in lessons:
                                        for key, value in lesson.items():
                                            if key == day:
                                                value.append({lektion: [x]})
                                                old_time = x
                                                continue
                                            if key == "Måndag" and day == "ndag":
                                                value.append({lektion: [x]})
                                                old_time = x
                                

                        break
        if day_lessons == []:
            continue

        

    # print(lessons)
    return lessons
        
def convert_time_lessons_to_csv(data, output_filename):
    flattened_data = [
        {'lektion': lesson_name, 'tid': time, 'dag': day}
        for day_data in data for day, lessons in day_data.items()
        for lesson in lessons for lesson_name, time in lesson.items()
    ]
    df = pd.DataFrame(flattened_data)
    df.to_csv(output_filename, index=False)
    return df

def create_combined_schedule():
    '''
    This function reads the lessons.csv file and combines the lessons for each day into a single schedule
    It then saves the combined schedule to a new CSV file in the "combined_schedule" folder
    :return: The combined schedule as a DataFrame
    '''
    # Define the days of the week
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
    
    # Read the lessons.csv file using pandas
    df = pd.read_csv("lessons.csv", encoding="utf-8")
    
    # Initialize a dictionary to store lessons by day
    schedule = {day: [] for day in days}

    for index, row in df.iterrows():
        lesson_name = row['lektion']
        time_info_str = row['tid']
        day = row['dag']

        # Manually parse the time_info_str to extract start time and end time
        time_info = ast.literal_eval(time_info_str)  # Safely parse the string into a list
        
        if len(time_info) == 3:
            start_time = datetime.strptime(time_info[0], '%H:%M')  # Convert start time to datetime object
            end_time = time_info[1]  # Keep end time as string for display
            schedule[day].append((start_time, end_time, lesson_name))
        else:
            print(f"Unexpected time format in line: {row}")

    # Create a DataFrame to hold the schedule
    max_rows = 0
    for day, lessons in schedule.items():
        # Sort lessons by start time
        lessons.sort(key=lambda x: x[0])  # Sort by datetime object of start time
        max_rows = max(max_rows, len(lessons))

    # Initialize a DataFrame with NaN values
    df_schedule = pd.DataFrame(index=range(max_rows), columns=days)

    # Fill the DataFrame with sorted lessons
    for day in days:
        for i, (start_time, end_time, lesson_name) in enumerate(schedule[day]):
            start_time_str = start_time.strftime('%H:%M')  # Convert back to string for display
            df_schedule.at[i, day] = f"{lesson_name} ({start_time_str}-{end_time})"
    
    # Create directory if it doesn't exist
    output_folder = "combined_schedule"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Save the DataFrame to a CSV file in the new folder "combined_schedule"
    df_schedule.to_csv(os.path.join(output_folder, "schedule.csv"), index=False, encoding="utf-8")

    return df_schedule

def create_class_schedule_from_combined_schedule(df):
    schedule = {}
    pupil_lessons_df = pd.read_csv("pupils_lessons.csv", encoding="utf-8")
    for day in df.columns:
        day_schedule = []
        for lesson in df[day].dropna():
            lesson_name, lesson_time = lesson.rsplit(' ', 1)
            lesson_time = lesson_time.strip('()')
            kurs_list = pupil_lessons_df[pupil_lessons_df['lektion'].str.contains(lesson_name)]['kurs'].unique()
            for kurs in kurs_list:
                class_dict = next((item for item in day_schedule if kurs in item), {kurs: []})
                class_dict[kurs].append({lesson_time: lesson_name})
                if class_dict not in day_schedule:
                    day_schedule.append(class_dict)
        if day_schedule:
            schedule[day] = day_schedule
    return schedule
    
    
def create_csv_for_each_class(schedule, classes):
    class_data = {}
    days_of_week = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]

    def convert_time_range_to_minutes(time_range):
        # Convert "HH:MM-HH:MM" to a tuple of start and end times in minutes
        start_time, end_time = time_range.split('-')
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        start_total_minutes = start_hour * 60 + start_minute
        end_total_minutes = end_hour * 60 + end_minute
        return start_total_minutes, end_total_minutes

    for day, classes in schedule.items():
        for class_dict in classes:
            for kurs, lessons in class_dict.items():
                if kurs not in class_data:
                    class_data[kurs] = {day: [] for day in days_of_week}
                end_times = []
                for lesson in lessons:
                    for time, subject in lesson.items():
                        start_time, end_time = convert_time_range_to_minutes(time)
                        # Check for overlapping times
                        class_data[kurs][day].append(f"{time}: {subject}")
                        end_times.append((start_time, end_time))  # Keep track of (start, end) times

    for kurs, data in class_data.items():
        max_lessons = max(len(lessons) for lessons in data.values())
        # Create DataFrame with uniform row numbers per day
        df = pd.DataFrame({day: data[day] + [''] * (max_lessons - len(data[day])) for day in days_of_week})

        # Replace NaN values with an empty string
        df.fillna('', inplace=True)

        # Ensure the output folder exists
        output_folder = "class_schedules"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Write DataFrame to CSV file
        df.to_csv(os.path.join(output_folder, f"{kurs}.csv"), index=False, encoding="utf-8-sig")
        print(f"Class schedule saved for: {kurs}")

if __name__ == "__main__":
    
    classes = get_classes()
    pupils, schema = get_pupils_ssn(classes)

    all_lessons = get_all_lessons(pupils, schema)
    names = get_pupil_names(pupils, schema)
    df = convert_to_csv(all_lessons, names, "pupils_lessons.csv")

    lessons = format_days_to_lessons(schema, df)
    convert_time_lessons_to_csv(lessons, "lessons.csv")
    df = create_combined_schedule()
    schedule = create_class_schedule_from_combined_schedule(df)
    create_csv_for_each_class(schedule, classes)