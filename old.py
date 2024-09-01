CLASSES = ["TE22", "TE23", "TE24", "EE22", "EE23", "EE24", "ES22", "ES23", "ES24"]

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

pupils, schema = get_pupils_ssn()

TE22 = [pupil for pupil in pupils if "TE22" in pupil]

def get_pupil_lessons(data):
    lessons = []
    for pupil in data:
        for key, value in pupil.items():
            pupil_lessons = []
            for line in schema:
                if value in line and key is not line.split(" ")[0]:
                    new_line = line.split(" ")
                    print(new_line)
                    break


get_pupil_lessons(TE22)