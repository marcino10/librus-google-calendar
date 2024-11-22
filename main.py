from credentials_librus import *
from librus_apix.client import new_client, Client, Token
from datetime import datetime, timedelta
from librus_apix.timetable import get_timetable
import google_authorize
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import re
import os

def get_librus_client():
    client: Client = new_client()

    # Now we update the token with client.get_token(u, p)
    _token: Token = client.get_token(login, password)  # this sets and returns token attribute

    # Now that we have our token updated we can work on saving it. This can be done by extracting the key.
    # A key is a combination of 2 authorization cookies Librus uses. Format: '{DZIENNIKSID:SDZIENNIKSID}'
    key = client.token.API_Key  # can be also done with str(client.token)

    # A token can be then created from such key or DZIENNIKSID/SDZIENNIKSID cookies
    token = Token(API_Key=key)

    # The token can then be just passed into new_client function
    client = new_client(token=token)

    return client


def change_time_by_minutes(time, minutes, operation='addition'):
    time_format = '%H:%M'
    if operation == 'addition':
        time = datetime.strptime(time, time_format)
        time += timedelta(minutes=minutes)
    elif operation == 'subtraction':
        time = datetime.strptime(time, time_format)
        time -= timedelta(minutes=minutes)
    else:
        raise ValueError('Invalid operation')
    return datetime.strftime(time, '%H:%M')


def get_time_blocks(exc_patterns, num_of_weeks=3):
    client = get_librus_client()

    today = datetime.now()
    monday_dates = []
    for i in range(0, num_of_weeks):
        day = today + timedelta(weeks=i)
        monday_dates.append(day - timedelta(days=day.weekday()))
    timetables = [get_timetable(client, date) for date in monday_dates]

    time_blocks = {}
    for timetable in timetables:
        day_count = 1
        for weekday in timetable:
            if datetime.strptime(weekday[0].date, '%Y-%m-%d').date() < today.date():
                continue
            has_start = False

            exc_subjects = [subject for subject in (exc_patterns[day_count]+exc_patterns[0])]

            for lesson in range(0, len(weekday)):
                if not has_start:
                    if weekday[lesson].subject != '' and weekday[lesson].subject not in exc_subjects:
                        start_time = weekday[lesson].date_from
                        start_time = change_time_by_minutes(start_time, 20, 'subtraction')
                        has_start = True
                elif weekday[lesson].subject == '' or weekday[lesson].subject in exc_subjects:
                    end_time = weekday[lesson - 1].date_to
                    end_time = change_time_by_minutes(end_time, 20, 'addition')
                    time_blocks[weekday[0].date] = [start_time, end_time]
                    break

            day_count += 1

    return time_blocks


def set_service(creds):
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def get_calendar_list(service):
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        calendar_entry_list = []
        for calendar_list_entry in calendar_list['items']:
            calendar_entry_list.append(calendar_list_entry)
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    return calendar_entry_list


def get_event_list(service, calendar_id):
    events = service.events().list(
        calendarId=calendar_id,
        timeMin=f"{datetime.now().date()}T00:00:00Z",
        q='school'
    ).execute()
    return events


def get_calendar_names(service):
    calendar_list = get_calendar_list(service)
    return [calendar['summary'] for calendar in calendar_list]


def get_calendar_id(service, calendar_name):
    calendar_list = get_calendar_list(service)
    for calendar in calendar_list:
        if calendar['summary'] == calendar_name:
            return calendar['id']


def set_events(service, time_blocks, calendar_id='primary'):
    for day, times in time_blocks.items():
        event = {
            'summary': 'School',
            'start': {
                'dateTime': f"{day}T{times[0]}:00",
                'timeZone': 'Europe/Warsaw'
            },
            'end': {
                'dateTime': f"{day}T{times[1]}:00",
                'timeZone': 'Europe/Warsaw'
            }
        }

        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))


def delete_past_events(events_list):
    current_date = datetime.now().date()

    events_list = [event for event in events_list if datetime.strptime(event, '%Y-%m-%d').date() >= current_date]

    return events_list


def get_event_date(event):
    return datetime.strftime(datetime.strptime(event['start']['dateTime'], '%Y-%m-%dT%H:%M:%S%z').date(), "%Y-%m-%d")


def get_events_json(events):
    events_json = {}
    for event in events:
        events_json[get_event_date(event)] = {
            'summary': event['summary'],
            'start': event['start']['dateTime'],
            'end': event['end']['dateTime']
        }
    return events_json


def get_changed_time_blocks(events, time_blocks):
    pattern = r"(?<=T)\d{2}:\d{2}"
    changed_time_blocks = {}
    for event in time_blocks.keys():
        if event in events.keys():
            if re.search(pattern, events[event]['start']).group() != time_blocks[event][0]\
                    or re.search(pattern, events[event]['end']).group() != time_blocks[event][1]:
                changed_time_blocks[event] = time_blocks[event]
        else:
            changed_time_blocks[event] = time_blocks[event]

    return changed_time_blocks


def create_files():
    if not os.path.exists('events.json'):
        with open('events.json', 'w') as events_file:
            json.dump({}, events_file, indent=4)
    if not os.path.exists('del_events.json'):
        with open('del_events.json', 'w') as del_events_file:
            json.dump([], del_events_file, indent=4)


def main():
    create_files()
    creds = google_authorize.main()
    # key is a weekday - it starts from 1 for Monday and ends at 7 for Sunday
    # for all days set key to 0
    exc_patterns = {
        0: ['Zajęcia z wychowawcą'],
        1: [],
        2: ['Godz. do dyspozycji dyrektora'],
        3: [],
        4: [],
        5: [],
        6: [],
        7: []
    }
    time_blocks = get_time_blocks(exc_patterns, 3)
    service = set_service(creds)
    calendar_id = get_calendar_id(service, 'Work')
    events = get_event_list(service, calendar_id)['items']
    events_json = get_events_json(events)

    with open('events.json', 'r') as events_file:
        prev_events_json = json.load(events_file)

    del_events = []
    for event in prev_events_json.keys():
        if event not in events_json.keys():
            del_events.append(event)

    with open('del_events.json', 'r') as del_events_file:
        del_events_file = json.load(del_events_file)

    del_events_file = delete_past_events(del_events_file)

    del_events = del_events + del_events_file

    for day in time_blocks.copy().keys():
        if day in del_events:
            del time_blocks[day]

    time_blocks = get_changed_time_blocks(events_json, time_blocks)

    set_events(service, time_blocks, calendar_id)
    with open('events.json', 'w') as events_file:
        json.dump(events_json, events_file, indent=4)
    with open('del_events.json', 'w') as del_events_file:
        json.dump(del_events, del_events_file, indent=4)

    # print calendar names
    # print(get_calendar_names(service))


if __name__ == "__main__":
    main()
