import pandas as pd
import os
import ast
from datetime import datetime
import re
import threading
import multiprocessing

class Schedule:
    def __init__(self, data, classes):
        self.text_file = data
        self.classes = classes
        
    def get_classes(self):
        current_year = datetime.now().year
        current_month = datetime.now().month
        if current_month < 8:
            current_year -= 1
        current_year = str(current_year)[2:]
        classes = [f"{cls}{year}" for cls in self.classes for year in range(int(current_year) - 2, int(current_year) + 1)]
        
        print(classes)
        return classes
    
    def get_pupils_ssn(self):
        pupils = []
        schema_lines = []

        # Regular expression to match 12-digit SSNs
        ssn_pattern = re.compile(r"\b\d{12}\b")
        
        # Combine class check into one expression to reduce repetitive checks
        class_pattern = re.compile(r"^(?:" + "|".join(self.classes) + r")")

        with open(self.text_file, "r", encoding="utf-8") as file:
            for line in file:
                schema_lines.append(line.strip())
                if class_pattern.match(line):
                    ssns = ssn_pattern.findall(line)
                    pupils.extend([{cls: ssn} for ssn in ssns for cls in self.classes if line.startswith(cls)])

        return pupils, schema_lines

    def get_all_lessons(self):
        lessons = []
        
        # Create a dictionary that excludes SSNs and strips whitespace
        schema_dict = {
            line.split("\t")[0].strip(): line.strip() for line in self.schema if not line.split("\t")[0].strip().isdigit()
        }

        # Process each pupil and their lessons
        for pupil in self.data:
            for cls, ssn in pupil.items():
                ssn = ssn.strip()  # Ensure SSN is clean
                pupil_lessons = [
                    {ssn: schema_dict[lesson_id].split("\t")[0].strip()}
                    for lesson_id, lesson_line in schema_dict.items() if ssn in lesson_line
                ]
                lessons.append({cls: pupil_lessons})

        return lessons

    def get_pupil_names(self):
        names = []
        track_row = 0
        for i, line in enumerate(self.schema):
            if "Student" in line:
                track_row = i
                break
        schema_dict = {line.split("\t")[0].strip(): line.strip() for line in self.schema[track_row-1:]}
        for pupil in self.data:
            for cls, ssn in pupil.items():
                ssn = ssn.strip()
                if ssn in schema_dict:
                    x = [item.strip() for item in schema_dict[ssn].split("\t") if item and "{" not in item]
                    if len(x) > 2:
                        name = f"{x[1]} {x[2]}"
                        names.append({ssn: name})
        return names
    
    def convert_to_csv(self, filename="pupils_lessons.csv"):
        flattened_data = [
            {
                'kurs': cls,
                'personnummer': ssn,
                'lektion': lesson_name,
                'namn': next((name[ssn] for name in self.names if ssn in name), '')
            }
            for lesson_dict in self.all_lessons for cls, pupil_lessons in lesson_dict.items()
            for lesson in pupil_lessons for ssn, lesson_name in lesson.items() if cls != lesson_name   
        ]
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False)
        return df
    
    def add_minutes_to_time(self, old_time, minutes_to_add):
        old_time_split = old_time.split(":")
        old_time_minutes = int(old_time_split[1])
        old_time_hours = int(old_time_split[0])
        new_time_minutes = old_time_minutes + int(minutes_to_add)
        new_time_hours = old_time_hours + new_time_minutes // 60
        new_time_minutes = new_time_minutes % 60
        return f"{new_time_hours:02}:{new_time_minutes:02}"
    
    def format_days_to_lessons(self, current_period):
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
        
        for i, line in enumerate(self.schema):
            day_lessons = []
            step = 0
            for day in days:
                if day in line:
                    for lektion in self.df["lektion"]:
                        if re.search(rf"\b{lektion}\b", line):
                            line_data = line.split("\t")
                            #check if period exists, or if there are not "P1" "P2" AND "P3" in the line
                            if current_period in line_data or ("P1" not in line_data and "P2" not in line_data and "P3" not in line_data):
                                step = False
                                old_time = ""
                                for i, x in enumerate(line_data):
                                    if step:
                                        step = False
                                        for lesson in lessons:
                                            for key, value in lesson.items():
                                                if key == day:
                                                    if ":" in old_time:
                                                        new_time = self.add_minutes_to_time(old_time, x)
                                                        value[-1][lektion].append(new_time)
                                                    value[-1][lektion].append(x)
                                                    
                                                    room = line_data[i+5]
                                                    value[-1][lektion].append(room)
                                                    
                                                    continue
                                                if key == "Måndag" and day == "ndag":
                                                    if ":" in old_time:
                                                        new_time = self.add_minutes_to_time(old_time, x)
                                                        value[-1][lektion].append(new_time)
                                                    value[-1][lektion].append(x)
                                                    
                                                    room = line_data[i+5]
                                                    value[-1][lektion].append(room)
                                                    
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
    
    def convert_time_lessons_to_csv(self, output_filename):        
        flattened_data = [
            {"lektion": lesson_name, "tid": [start_time, end_time, total_minutes], "dag": day, "rum": room}
            for day_data in self.lessons
            for day, lessons in day_data.items()
            for lesson in lessons
            for lesson_name, time_and_room in lesson.items()
            for start_time, end_time, total_minutes, room in [time_and_room]
        ]
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_filename, index=False)
        return df
    
    def create_combined_schedule(self):
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        df = pd.read_csv("lessons.csv", encoding="utf-8")
        schedule = {day: [] for day in days}
        for index, row in df.iterrows():
            lesson_name = row['lektion']
            time_info_str = row['tid']
            day = row['dag']
            room = row['rum']
            
            time_info = ast.literal_eval(time_info_str)
            if len(time_info) == 3:
                start_time = datetime.strptime(time_info[0], '%H:%M')
                end_time = time_info[1]
                schedule[day].append((start_time, end_time, lesson_name, room))
            else:
                print(f"Unexpected time format in line: {row}")
        max_rows = 0
        for day, lessons in schedule.items():
            lessons.sort(key=lambda x: x[0])
            max_rows = max(max_rows, len(lessons))
        df_schedule = pd.DataFrame(index=range(max_rows), columns=days)
        for day in days:
            for i, (start_time, end_time, lesson_name, room) in enumerate(schedule[day]):
                start_time_str = start_time.strftime('%H:%M')
                # Handle missing room information
                if pd.isna(room) or room == '':
                    room_str = ''
                else:
                    room_str = f",{room}"
                df_schedule.at[i, day] = f"{lesson_name} ({start_time_str}-{end_time}{room_str})"
        output_folder = "combined_schedule"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        df_schedule.to_csv(os.path.join(output_folder, "schedule.csv"), index=False, encoding="utf-8")
        return df_schedule
    
    def create_class_schedule_from_combined_schedule(self, df):
        schedule = {}
        pupil_lessons_df = pd.read_csv("pupils_lessons.csv", encoding="utf-8")
        # Adjusted regular expression to handle optional room
        lesson_pattern = r'^(.*?) \(([^-]+)-([^\),]+)(?:,([^)]+))?\)$'
        for day in df.columns:
            day_schedule = []
            for lesson in df[day].dropna():
                match = re.match(lesson_pattern, lesson)
                if match:
                    lesson_name = match.group(1).strip()
                    start_time = match.group(2).strip()
                    end_time = match.group(3).strip()
                    room = match.group(4)  # May be None if room is missing
                    if room:
                        room = room.strip()
                else:
                    continue  # Skip if the lesson string doesn't match the expected format
                # Get the list of courses (kurs) associated with the lesson
                kurs_list = pupil_lessons_df[pupil_lessons_df['lektion'] == lesson_name]['kurs'].unique()
                for kurs in kurs_list:
                    # Find existing class_dict or create a new one
                    class_dict = next((item for item in day_schedule if kurs in item), None)
                    if class_dict is None:
                        class_dict = {kurs: []}
                        day_schedule.append(class_dict)
                    # Build lesson info
                    lesson_info = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'lesson_name': lesson_name,
                    }
                    if room:
                        lesson_info['room'] = room
                    class_dict[kurs].append(lesson_info)
            if day_schedule:
                schedule[day] = day_schedule
        return schedule

    def create_csv_for_each_class(self, schedule):
        class_data = {}
        days_of_week = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]

        def convert_time_to_minutes(time_str):
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute

        for day in days_of_week:
            if day in schedule:
                classes = schedule[day]
                for class_dict in classes:
                    for kurs, lessons in class_dict.items():
                        if kurs not in class_data:
                            class_data[kurs] = {d: [] for d in days_of_week}
                        for lesson in lessons:
                            start_time = lesson['start_time']
                            end_time = lesson['end_time']
                            lesson_name = lesson['lesson_name']
                            lesson_name = lesson_name.replace("�", "ä")
                            
                            room = lesson.get('room', None)
                            time_range = f"{start_time}-{end_time}"
                            # Format the lesson string including room if available
                            if room:
                                lesson_str = f"{time_range}: {lesson_name} ({room})"
                            else:
                                lesson_str = f"{time_range}: {lesson_name}"
                            class_data[kurs][day].append({
                                'start_minutes': convert_time_to_minutes(start_time),
                                'lesson_str': lesson_str
                            })

        # Sort lessons by start time for each day and class
        for kurs, days in class_data.items():
            for day in days_of_week:
                days[day] = sorted(days[day], key=lambda x: x['start_minutes'])
                # Replace the list of dicts with list of lesson strings
                days[day] = [item['lesson_str'] for item in days[day]]

        # Write CSV files for each class
        for kurs, data in class_data.items():
            max_lessons = max(len(lessons) for lessons in data.values())
            df = pd.DataFrame({
                day: data[day] + [''] * (max_lessons - len(data[day]))
                for day in days_of_week
            })
            df.fillna('', inplace=True)
            output_folder = "class_schedules"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            df.to_csv(
                os.path.join(output_folder, f"{kurs}.csv"),
                index=False,
                encoding="utf-8-sig"
            )
            print(f"Class schedule saved for: {kurs}")
        
    def run_schedule_operations(self):
        # Step 1: Run get_classes and get_pupils_ssn without multiprocessing since they are prerequisites
        self.classes = self.get_classes()
        self.data, self.schema = self.get_pupils_ssn()

        # Step 2: Use multiprocessing for CPU-bound tasks
        with multiprocessing.Pool() as pool:
            # Collect results from the multiprocessing tasks
            results = pool.starmap(self._get_attr_result, [
                ('get_all_lessons',),
                ('get_pupil_names',),
            ])

        # Assign the results to the corresponding attributes
        self.all_lessons = results[0]  # Result from get_all_lessons
        self.names = results[1]        # Result from get_pupil_names

        # Step 3: Continue with dependent operations after multiprocessing tasks finish
        self.df = self.convert_to_csv("pupils_lessons.csv")
        self.lessons = self.format_days_to_lessons(PERIOD)
        self.convert_time_lessons_to_csv("lessons.csv")
        self.df = self.create_combined_schedule()
        self.schedule = self.create_class_schedule_from_combined_schedule(self.df)
        self.create_csv_for_each_class(self.schedule)

    def _get_attr_result(self, func_name):
        """Helper function to run a method and return its result using multiprocessing."""
        func = getattr(self, func_name)
        return func()

# In the main block

PERIOD = "P2"

if __name__ == "__main__":
    start_time = datetime.now()

    schedule = Schedule("schema.txt", ["TE", "EE", "ES"])
    schedule.run_schedule_operations()

    end_time = datetime.now()
    print(f"Time taken with multiprocessing: {end_time - start_time}")