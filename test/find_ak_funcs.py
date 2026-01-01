import akshare as ak
import inspect

def find_functions(keywords):
    for name, obj in inspect.getmembers(ak):
        if inspect.isfunction(obj):
            for keyword in keywords:
                if keyword in name:
                    print(f"Function: {name}")
                    try:
                        print(f"Docstring: {obj.__doc__[:200]}...") 
                    except:
                        pass
                    print("-" * 20)

print("Searching for forecast/predict/institute/report related functions...")
find_functions(['forecast', 'predict', 'institute', 'report'])
