# pip install librus-apix
from credentials import *
from librus_apix.client import new_client, Client, Token
from datetime import datetime
from librus_apix.timetable import get_timetable

def main():
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

    monday_date = '2024-11-11'
    monday_datetime = datetime.strptime(monday_date, '%Y-%m-%d')
    timetable = get_timetable(client, monday_datetime)
    print(timetable[2])

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
                    print(start_time)
            if weekday[lesson].subject == '' and has_start:
                end_time = weekday[lesson-1].date_to
                time_blocks[weekday[0].date] = [start_time, end_time]
                break

    print(time_blocks)


if __name__ == "__main__":
    main()
