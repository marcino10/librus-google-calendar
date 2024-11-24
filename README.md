# Librus - Google Calendar Integration
### This project allows you to create time-blocks events in your Google Calendar based on your Librus timetable.

## Project Setup
1. Clone this repository
2. [Create a new project in Google Cloud Console](https://medium\.com/@ayushbhatnagarmit/supercharge-your-scheduling-automating-google-calendar-with-python-87f752010375)
3. Download the credentials.json file from Google Cloud and put it in the root directory of the project
4. Install required packages from requirements.txt
5. Set up config.json:
```json
{
  // key is the number of the day of the week (0 - Monday, 1 - Tuesday, ..., 6 - Sunday).
  // 0 is for all days.
  "exc_patterns": {
        "0": ["Name of the subject"],
        "1": [],
        "2": [],
        "3": [],
        "4": [],
        "5": [],
        "6": [],
        "7": []
  },
  "num_of_weeks": 3,
  // put your librus credentials here
  "librus_login": "login",
  "librus_password": "password"
}
```
6. Run the main.py script
