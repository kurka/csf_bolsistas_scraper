import pandas as pd
import sys

if len(sys.argv) != 3:
    print("Usage: json2spreadsheet students_date.json universities_date.json")

else:
    writer = pd.ExcelWriter("Students CSF.xlsx")
    for name in sys.argv[1:3]:
        pd.read_json(name).to_excel(writer, name.split(".")[0]+".xlsx", index=False)

    writer.save()



