import pandas as pd
import os
import ast
from datetime import datetime
import re

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
        
        return classes
    
    def get_pupils_ssn(self):
        pupils = []
        schema_lines = []
        with open(self.text_file, "r") as file:
            for line in file:
                schema_lines.append(line.strip())
                for cls in self.classes:
                    if line.startswith(cls):
                        ssns = line.split(",")[1:]
                        pupils.extend([{cls: ssn} for ssn in ssns])
        return pupils, schema_lines
    
    def get_all_lessons(self):
        lessons = []
        schema_dict = {line.split("\t")[0]: line for line in self.schema}
        for pupil in self.data:
            for cls, ssn in pupil.items():
                pupil_lessons = [{ssn: schema_dict.get(lesson_id).split("\t")[0]} for lesson_id in schema_dict if ssn in schema_dict[lesson_id] and ssn != lesson_id]
                lessons.append({cls: pupil_lessons})
        return lessons
    
    def get_pupil_names(self):
        names = []
        track_row = 0
        for i, line in enumerate(self.schema):
            if "Student" in line:
                track_row = i
                break
        schema_dict = {line.split("\t")[0]: line for line in self.schema[track_row:]}
        for pupil in self.data:
            for cls, ssn in pupil.items():
                if ssn in schema_dict:
                    x = [x for x in schema_dict[ssn].split("\t") if x and "{" not in x]
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
    
    def format_days_to_lessons(self):
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
                                        for lesson in lessons:
                                            for key, value in lesson.items():
                                                if key == day:
                                                    if ":" in old_time:
                                                        new_time = self.add_minutes_to_time(old_time, x)
                                                        value[-1][lektion].append(new_time)
                                                    value[-1][lektion].append(x)
                                                    continue
                                                if key == "Måndag" and day == "ndag":
                                                    if ":" in old_time:
                                                        new_time = self.add_minutes_to_time(old_time, x)
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
        return lessons
    
    def convert_time_lessons_to_csv(self, output_filename):
        flattened_data = [
            {'lektion': lesson_name, 'tid': time, 'dag': day}
            for day_data in self.lessons for day, lessons in day_data.items()
            for lesson in lessons for lesson_name, time in lesson.items()
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
            time_info = ast.literal_eval(time_info_str)
            if len(time_info) == 3:
                start_time = datetime.strptime(time_info[0], '%H:%M')
                end_time = time_info[1]
                schedule[day].append((start_time, end_time, lesson_name))
            else:
                print(f"Unexpected time format in line: {row}")
        max_rows = 0
        for day, lessons in schedule.items():
            lessons.sort(key=lambda x: x[0])
            max_rows = max(max_rows, len(lessons))
        df_schedule = pd.DataFrame(index=range(max_rows), columns=days)
        for day in days:
            for i, (start_time, end_time, lesson_name) in enumerate(schedule[day]):
                start_time_str = start_time.strftime('%H:%M')
                df_schedule.at[i, day] = f"{lesson_name} ({start_time_str}-{end_time})"
        output_folder = "combined_schedule"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        df_schedule.to_csv(os.path.join(output_folder, "schedule.csv"), index=False, encoding="utf-8")
        return df_schedule
    
    def create_class_schedule_from_combined_schedule(self, df):
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
    
    def create_csv_for_each_class(self, schedule):
        class_data = {}
        days_of_week = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        def convert_time_range_to_minutes(time_range):
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
                            class_data[kurs][day].append(f"{time}: {subject}")
                            end_times.append((start_time, end_time))
        for kurs, data in class_data.items():
            max_lessons = max(len(lessons) for lessons in data.values())
            df = pd.DataFrame({day: data[day] + [''] * (max_lessons - len(data[day])) for day in days_of_week})
            df.fillna('', inplace=True)
            output_folder = "class_schedules"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            df.to_csv(os.path.join(output_folder, f"{kurs}.csv"), index=False, encoding="utf-8-sig")
            print(f"Class schedule saved for: {kurs}")
            
    def run(self):
        self.classes = self.get_classes()
        self.data, self.schema = self.get_pupils_ssn()
        self.all_lessons = self.get_all_lessons()
        self.names = self.get_pupil_names()
        self.df = self.convert_to_csv("pupils_lessons.csv")
        self.lessons = self.format_days_to_lessons()
        self.convert_time_lessons_to_csv("lessons.csv")
        self.df = self.create_combined_schedule()
        self.schedule = self.create_class_schedule_from_combined_schedule(self.df)
        self.create_csv_for_each_class(self.schedule)

if __name__ == "__main__":
    schedule = Schedule("schema.txt", ["TE", "EE", "ES"])
    schedule.run()