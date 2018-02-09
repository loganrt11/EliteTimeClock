import os
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from time import gmtime, strftime, time
import datetime

def reminder_SMS(command):
    week_day = datetime.datetime.today().weekday()
    employee_dict = {y:x for x,y in getEmployeeDict().items()}
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    client_gsheets = signinGSheets()
    book = client_gsheets.open('Elite Time Clock (' + strftime("%Y", gmtime()) + ')')
    sh = get_sheet(book)
    if command == 'time in':
        col = 3
    if command == 'time out':
        col = 4
    for i in range(9, 121, 16):
        person = sh.cell(i, 3).value
        if not person == '':
            person = person + '(employee)'
            if week_day > 2:
                row_add = week_day - 1
            else:
                row_add = week_day + 6
            row = i + row_add
            if sh.cell(row, col).value == '':
                if command == 'time in':
                    print(employee_dict.get(person))
                    client.api.account.messages.create(
                        to = employee_dict.get(person),
                        from_ = "+14694143676",
                        body = 'This is a reminder that you have not clocked in today.')
                if command == 'time out':
                    client.api.account.messages.create(
                        to = employee_dict.get(person),
                        from_ = "+14694143676",
                        body = "This is a reminder that you have not clocked out today. Also be sure to send your stroke count if you have not")

def getEmployeeDict():
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    verified_numbers = {}
    for caller_id in client.outgoing_caller_ids.list():
        verified_numbers[caller_id.phone_number] = caller_id.friendly_name
    return verified_numbers

def signinGSheets():
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/pi/Desktop/EliteTimeClock/GoogleSheetsSecrets.json', scope)
    client = gspread.authorize(creds)
    return client

# returns sheet based on what day it is
def get_sheet(book):
   if int( strftime("%w", gmtime())) > 3:                                                         # if day is Thu-Sun
        sheet_number = int(strftime("%W", gmtime())) - 1
   else:                                                                                    # if day is Mon-Wed
        sheet_number = int(strftime("%W", gmtime())) - 2
   sheet = book.get_worksheet(sheet_number)
   return sheet


if __name__ == '__main__':
    reminder_SMS('time out')
