import pandas as pd
import os
import ast
from datetime import datetime

# MAKE THIS DYNAMIC BY TAKING THE DATE - 3 AND -2 AND -1 KIND OF U GET IT
CLASSES = ["TE22", "TE23", "TE24", "EE22", "EE23", "EE24", "ES22", "ES23", "ES24", "TE4"]

def get_pupils_ssn():
    pupils = []
    with open("./schema.txt", "r") as file:
        schema = file.read()
        for line in schema.split("\n"):
            for cls in CLASSES:
                if line[:4] == cls:
                    ssns = line.split(",")[1:]


                    x = [{cls: ssn} for ssn in ssns]
                    pupils.extend(x)


    return pupils, schema.split("\n")

def get_all_lessons(data):
    lessons = []
    for pupil in data:
        for key, value in pupil.items():
            pupil_lessons = []
            for line in schema:
                if value in line and value != line.split("\t")[0]:
                    pupil_lessons.append({value: line.split("\t")[0]})

            lessons.append({key: pupil_lessons})

    return lessons

def get_pupil_names(data):
    names = []
    track_row = 0
    with open("./schema.txt", "r") as file:
        schema = file.read()
        for i, line in enumerate(schema.split("\n")):
            if "Student" in line:
                track_row = i
                break

    for pupil in data:
        # iterate from the track row
        for cls, value in pupil.items():
            for line in schema.split("\n")[track_row:]:
                if value in line.split("\t")[0]:
                    x = [x for x in line.split("\t") if x and not "{" in x]
                    name = x[1] + " " + x[2]

                    names.append({value: name})

    
    return names

def convert_to_csv(data, filename="pupils_lessons.csv"):
    flattened_data = []
    for lesson_dict in data:
        for cls, pupil_lessons in lesson_dict.items():
            for lesson in pupil_lessons:
                for ssn, lesson_name in lesson.items():
                    if cls == lesson_name:
                        continue

                    name_to_append = ""
                    for name in names:
                        for ssn_key, name_value in name.items():
                            if ssn == ssn_key:
                                name_to_append = name_value
                                break


                    flattened_data.append({
                        'kurs': cls,
                        'personnummer': ssn,
                        'lektion': lesson_name,
                        'namn': name_to_append
                    })

    
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
    if ":" in old_time:
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
    '''
    Function to convert the time lessons data to a CSV file
    It works by flattening (converting to a list of dictionaries) the data structure
    and then converting it to a DataFrame using pandas, which is then saved to a CSV file
    :param data: The time lessons data to convert
    :param output_filename: The name of the output CSV file
    '''
    
    
    flattened_data = []
    
    # Flatten the data structure to a list of dictionaries
    for day in data:
        # Iterate over each day in the data
        for key, value in day.items():
            # Iterate over each lesson in the day
            for lesson in value:
                # Iterate over each lesson's name and time
                for lesson_name, time in lesson.items():
                    # Append the lesson data to the flattened list
                    flattened_data.append({
                        'lektion': lesson_name,
                        'tid': time,
                        'dag': key
                    })

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
    '''
    This function takes the combined schedule DataFrame and creates a schedule for each class
    It then saves the class schedules to separate CSV files in the "class_schedules" folder
    :param df: The combined schedule DataFrame
    :return: The class schedule dictionary
    '''
    schedule = {}

    for day in df.columns:  # Iterate over each day in the DataFrame
        day_schedule = []  # Initialize the list to hold all classes for the day

        for i, lesson in enumerate(df[day]):  # Iterate over each lesson for the day
            if pd.notnull(lesson):  # Check if the lesson is not NaN
                lesson_name = " ".join(lesson.split(" ")[:-1])
                lesson_time = lesson.split(" ")[-1]
                kurs_list = []  # To keep track of all classes (kurs) for this lesson

                pupil_lessons_df = pd.read_csv("pupils_lessons.csv", encoding="utf-8")  # Load pupil lessons data

                for index, row in pupil_lessons_df.iterrows():
                    if lesson_name in row['lektion']:  # Match the lesson name with the data in pupils_lessons.csv
                        kurs = row['kurs']
                        if kurs not in kurs_list:  # Only add unique kurs
                            kurs_list.append(kurs)
                            # Check if the kurs is already in the day_schedule
                            kurs_found = False
                            for class_dict in day_schedule:
                                if kurs in class_dict:
                                    class_dict[kurs].append({lesson_time: lesson_name})  # Append new time and lesson
                                    kurs_found = True
                                    break
                            if not kurs_found:  # If kurs was not found, create a new entry
                                day_schedule.append({kurs: [{lesson_time: lesson_name}]})

        if day_schedule:  # Only add to the schedule if there's something to add
            schedule[day] = day_schedule

    print(schedule)

    return schedule
    
    
def create_csv_for_each_class(schedule):
    '''
    This function takes the class schedule dictionary and creates a separate CSV file for each class
    It saves the CSV files in the "class_schedules" folder
    params: schedule: The class schedule dictionary
    returns: None
    Note:
    - The current implementation does not handle overlapping lessons correctly
    - If a wrongly assigned lesson is present before the correct overlapping one, the output will be incorrect
    '''
    
    # Dictionary to hold the data for each class
    class_data = {}

    # Days of the week to be used as columns in the DataFrame
    days_of_week = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]

    # Function to convert time ranges to a tuple of integers representing start and end in minutes
    def convert_time_range_to_minutes(time_range):
        # Clean the time range string by removing any extraneous characters like parentheses
        time_range = time_range.replace("(", "").replace(")", "").strip()
        start_time, end_time = time_range.split('-')
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        return (start_hour * 60 + start_minute, end_hour * 60 + end_minute)

    # Iterate through each day and its corresponding lessons in the schedule
    for day in days_of_week:
        if day in schedule:  # Only process days that are present in the schedule
            classes = schedule[day]
            for class_dict in classes:
                for kurs, lessons in class_dict.items():
                    if kurs not in class_data:
                        # Initialize an empty dictionary for each class to collect lessons per day
                        class_data[kurs] = {day: [] for day in days_of_week}

                    # Initialize a list to track end times of lessons to check for overlaps
                    end_times = []

                    # Collect each lesson under the correct day
                    for lesson in lessons:
                        for time, subject in lesson.items():
                            # Convert lesson time to start and end minutes
                            start_time, end_time = convert_time_range_to_minutes(time)

                            # Check for overlap with any previous lesson's end time
                            if any(start_time < e for e in end_times):
                                continue

                            # Append the lesson to the correct day list in the class's dictionary
                            class_data[kurs][day].append(f"{time}: {subject}")

                            # Update the end times list with the current lesson's end time
                            end_times.append(end_time)

    # Create DataFrames for each class from the collected data
    for kurs, data in class_data.items():
        # Determine the maximum number of lessons any day has to balance rows
        max_lessons = max(len(lessons) for lessons in data.values())

        # Create a DataFrame with the same number of rows for each day
        df = pd.DataFrame({day: data[day] + [''] * (max_lessons - len(data[day])) for day in days_of_week})

        # Fill any NaN values with an empty string to avoid writing NaNs in CSV
        df.fillna('', inplace=True)

        # Ensure the output folder exists
        output_folder = "class_schedules"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Write DataFrame to CSV file
        df.to_csv(os.path.join(output_folder, f"{kurs}.csv"), index=False, encoding="utf-8-sig")
        print(f"Class schedule saved for: {kurs}")


if __name__ == "__main__":
    pupils, schema = get_pupils_ssn()

    all_lessons = get_all_lessons(pupils)
    names = get_pupil_names(pupils)
    df = convert_to_csv(all_lessons)

    lessons = format_days_to_lessons(schema, df)
    convert_time_lessons_to_csv(lessons, "lessons.csv")
    df = create_combined_schedule()
    schedule = create_class_schedule_from_combined_schedule(df)
    create_csv_for_each_class(schedule)