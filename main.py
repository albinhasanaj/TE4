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
                for lektion in df["lektion"]:
                    if lektion in line:
                        line_data = line.split("\t")

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
                                                    old_time_split = old_time.split(":")
                                                    old_time_minutes = int(old_time_split[1])
                                                    old_time_hours = int(old_time_split[0])
                                                    new_time_minutes = old_time_minutes + int(x)

                                                    # Adjust hours and minutes correctly
                                                    new_time_hours = old_time_hours + new_time_minutes // 60
                                                    new_time_minutes = new_time_minutes % 60

                                                    # Format the new time correctly
                                                    new_time = f"{new_time_hours:02}:{new_time_minutes:02}"
                                                    value[-1][lektion].append(new_time)
                                                value[-1][lektion].append(x)
                                                continue
                                            if key == "Måndag" and day == "ndag":
                                                if ":" in old_time:
                                                    old_time_split = old_time.split(":")
                                                    old_time_minutes = int(old_time_split[1])
                                                    old_time_hours = int(old_time_split[0])
                                                    new_time_minutes = old_time_minutes + int(x)

                                                    # Adjust hours and minutes correctly
                                                    new_time_hours = old_time_hours + new_time_minutes // 60
                                                    new_time_minutes = new_time_minutes % 60

                                                    # Format the new time correctly
                                                    new_time = f"{new_time_hours:02}:{new_time_minutes:02}"
                                                    value[-1][lektion].append(new_time)

                                                value[-1][lektion].append(x)

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
    flattened_data = []
    for day in data:
        for key, value in day.items():
            for lesson in value:
                for lesson_name, time in lesson.items():
                    flattened_data.append({
                        'lektion': lesson_name,
                        'tid': time,
                        'dag': key
                    })

    df = pd.DataFrame(flattened_data)
    df.to_csv(output_filename, index=False)

    return df

def create_combined_schedule():
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


if __name__ == "__main__":
    pupils, schema = get_pupils_ssn()

    all_lessons = get_all_lessons(pupils)
    names = get_pupil_names(pupils)
    df = convert_to_csv(all_lessons)

    lessons = format_days_to_lessons(schema, df)
    convert_time_lessons_to_csv(lessons, "lessons.csv")
    df = create_combined_schedule()
    print(df)