def get_pupil_names(self):
    names = []
    track_row = 0
    for i, line in enumerate(self.schema):
        if "Student" in line:
            track_row = i
            break
    schema_dict = {line.split("\t")[0]: line for line in self.schema[track_row-1:]}
    for pupil in self.data:
        for cls, ssn in pupil.items():
            # print("CLS:", cls, "SSN:", ssn)
            if ssn in schema_dict:
                x = [x for x in schema_dict[ssn].split("\t") if x and "{" not in x]
                if len(x) > 2:
                    name = f"{x[1]} {x[2]}"
                    names.append({ssn: name})
    return names
