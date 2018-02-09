from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from time import gmtime, strftime, time
import time
from datetime import datetime, timedelta


def newTimeSheet():
    strftime("%m/%d/%Y", gmtime())
    client = signinGSheets()
    employee_list = getEmployeeList()
    book = client.open('Elite Time Clock (' + strftime("%Y", gmtime()) + ')')
    newsh = get_sheet(book)
    l = 9
    k = 11
    for i in range(0, len(employee_list), 1):
        if employee_list[i].endswith("(employee)"):
            employee_list[i] = employee_list[i][:-10]
            newsh.update_acell('C' + str(l), employee_list[i])
            newsh.update_cell(9, k, employee_list[i])
            newsh.update_cell(9, k, employee_list[i])
            newsh.update_cell(23, k, employee_list[i])
            l = l + 16
            k = k +1
    date = datetime.now()
    for i in range(0, 8 , 1):
        starter_cell = 11
        starter_cell = starter_cell + (16*i)
        for j in range(0, 7, 1):
            input_row = starter_cell + j
            input_date = date + timedelta(days=j)
            newsh.update_cell(input_row, 1, str(input_date)[5:10])

def signinGSheets():
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/pi/Desktop/EliteTimeClock/GoogleSheetsSecrets.json', scope)
    client = gspread.authorize(creds)
    return client

def getEmployeeList():
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    employee_list = []
    for caller_id in client.outgoing_caller_ids.list():
        employee_list.append(caller_id.friendly_name)
    return employee_list

# returns sheet based on what day it is
def get_sheet(book):
   if int( strftime("%w", gmtime())) > 3:                                                         # if day is Thu-Sun
        sheet_number = int(strftime("%W", gmtime())) - 1
   else:                                                                                    # if day is Mon-Wed
        sheet_number = int(strftime("%W", gmtime())) - 2
   sheet = book.get_worksheet(sheet_number)
   return sheet


if __name__ == '__main__':
    newTimeSheet()
