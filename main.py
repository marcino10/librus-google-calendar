from credentials_librus import *
from librus_apix.client import new_client, Client, Token
from datetime import datetime, timedelta
from librus_apix.timetable import get_timetable
import google_authorize
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_time_blocks():
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

    today = datetime.now().date()
    monday_date = str(today - timedelta(days=today.weekday()))
    monday_date = datetime.strptime(monday_date, '%Y-%m-%d')
    timetable = get_timetable(client, monday_date)
    # print(timetable[1])

    time_blocks = {}
    for weekday in timetable:
        start_time = None
        end_time = None
        has_start = False
        for lesson in range(0, len(weekday)):
            if weekday[lesson].subject != '':
                if not has_start:
                    start_time = weekday[lesson].date_from
                    has_start = True
            if weekday[lesson].subject == '' and has_start:
                end_time = weekday[lesson - 1].date_to
                time_blocks[weekday[0].date] = [start_time, end_time]
                break
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


def get_calendar_names(service):
    calendar_list = get_calendar_list(service)
    return [calendar['summary'] for calendar in calendar_list]


def get_calendar_id(service, calendar_name):
    calendar_list = get_calendar_list(service)
    for calendar in calendar_list:
        if calendar['summary'] == calendar_name:
            return calendar['id']


def set_events(time_blocks, service):
    # for testing
    temp_time_blocks = time_blocks.copy()
    for day, times in time_blocks.items():
        if day == '2024-11-12':
            continue
        else:
            temp_time_blocks.pop(day)
    time_blocks = temp_time_blocks
    print (time_blocks)
    #

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

        event = service.events().insert(calendarId='Work', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))


def main():
    creds = google_authorize.main()
    time_blocks = get_time_blocks()
    service = set_service(creds)
    print(get_calendar_names(service))
    calendar_id = get_calendar_id(service,'Work')
    print(calendar_id)
    # set_events(time_blocks, service)


if __name__ == "__main__":
    main()
