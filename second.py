import os
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
from time import gmtime, strftime, time
import time
import threading
import datetime
import pickle

#-----------------------------------------------------------------------------------------------------------------------
#---------------------------------------SMS FUNCTIONS-------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------

# function to read what the sms contains and who it's from so it can decide what to do with it
def sms_distribute(From, Body):
    verified_numbers = getEmployeeDict()
    if From in verified_numbers:
        if verified_numbers.get(From).endswith('(employee)'):               # sends to employee function
            employee_SMSprocess(From, Body)
        if not verified_numbers.get(From).endswith('(employee)'):           # sends to superior function
            superior_SMSprocess(From, Body)

# function to process sms from employees and figure out what it means
def employee_SMSprocess(From, Body):
    verified_numbers = getEmployeeDict()
    employee_list = getEmployeeList()
    Body = Body.lower()
    error = False
    for i in range(0, len(employee_list), 1):                       # determining who the action is for
        employee_list[i] = employee_list[i].lower()
        employee_list[i] = employee_list[i].replace('(employee)', '')
        if employee_list[i] in Body:
            person = employee_list[i]
            Body.replace(employee_list[i], "")
            break
    else:
        tempBody = Body.split(' ')
        if len(tempBody) < 2:
            error_SMS(From, 'addToSheets fail')
            error = True
        elif tempBody[0].isalpha() and tempBody[1].isalpha() and len(tempBody[0]) > 3 and len(tempBody[1]) > 3:
            error_SMS(From, 'name')
            error = True
        else:
            person = verified_numbers.get(From).replace('(employee)', '')
    if ":" in Body:
        action = 'time'
        Body = Body.split(" ")
        for i in range(0, len(Body), 1):
            if len(Body[i]) < 5 and ":" in Body[i]:                 # time
                target = Body[i]
                pass
            if "in" in Body[i] or "out" in Body[i]:                 # time in or time out
                target2 = Body[i]
                target3 = 'none'
    else:
        action = 'stroke'
        Body = Body.split(" ")
        for i in range(0, len(Body), 1):
            if len(Body[i]) < 5 and Body[i].isdigit():              # stroke count
                target = Body[i]
                pass
            if len(Body[i]) == 8 and Body[i].isdigit():             # set number
                target2 = Body[i]
                pass
            if 'trailer' in Body[i]:                                # trailer number
                target3 = Body[i+1]
                pass
    if error == False:
        try:
            addToSheets(person, action, target, target2, target3)
            error_SMS(From, 'success')
        except:
            error_SMS(From, 'addToSheets fail')

# function to process sms from superiors and figure out what it means
def superior_SMSprocess(From, Body):
    Body = Body.lower()
    if Body == 'retrieve':
        send_stored_mesg()

# checks what has been inputted in google sheets and reminds with SMS if something missing
def reminder_SMS(command):
    week_day = datetime.datetime.today().weekday()
    employee_dict = {y:x for x,y in getEmployeeDict().items()}
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    client_gsheets = signinGSheets()
    spread = client_gsheets.open('Insealation Employee Time Clock (' + strftime("%Y", gmtime()) + ')')
    sh = spread.get_worksheet(0)
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

# responds to sender to state if message worked or if error occured
def error_SMS(sender, error):
    if error == 'addToSheets fail':
        mesg = 'Time clock entry failed. Please send message in one of the following formats:\n"John Smith 7:30 clock in"\n"John Smith 720 trailer A 92301243"\n\nIf the message is for yourself you do not have to include a name.'
    if error == 'name':
        mesg = 'Given name was not found.'
    if error == 'success':
        mesg = 'Time clock entry was sucecssful.'
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    client.api.account.messages.create(
        to = sender,
        from_ = "+14694143676",
        body = mesg)

# sends stored messages to Superior
def send_stored_mesg():
    with open('MessageStorage.txt', 'rb') as rfp:
        messages = pickle.load(rfp)
    text = ''
    for i in range(0, len(messages), 1):
        text = text + '\n\n' + messages[i]
    print(text)
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    if len(messages) > 0:
        client.api.account.messages.create(
            to = "+19032290832",
            from_ = "+14694143676",
            body = text)



#---------------------------------------GENERIC FUNCTIONS---------------------------------------------------------------

# retrieves and returns dictionary of employees and their numbers
def getEmployeeDict():
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    verified_numbers = {}
    for caller_id in client.outgoing_caller_ids.list():
        verified_numbers[caller_id.phone_number] = caller_id.friendly_name
    return verified_numbers

# retrieves and returns list of employee names
def getEmployeeList():
    account_sid = "ACfd3f5425de42d8f4c28004b23af8045c"
    auth_token = "37fd8c602eb60a1fb3b7854848056909"
    client = Client(account_sid, auth_token)
    employee_list = []
    for caller_id in client.outgoing_caller_ids.list():
        employee_list.append(caller_id.friendly_name)
    return employee_list

# stores recieved messages
def message_storage(From, Body):
    verified_numbers = getEmployeeDict()
    if '(employee)' in verified_numbers.get(From):
        from_name = verified_numbers.get(From).replace('(employee)', '')
    elif not '(employee)' in verified_numbers.get(From):
        from_name = verified_numbers.get(From)
    new_string = '"' + Body + '"' + ' (' + from_name + ') (' + str(strftime("%m/%d", gmtime())) + ')'
    messages = []
    if os.path.getsize('MessageStorage.txt') > 0 :
        with open('MessageStorage.txt', 'rb') as rfp:
            messages = pickle.load(rfp)
    messages.append(new_string)
    with open('MessageStorage.txt', 'wb') as wfp:
        pickle.dump(messages, wfp)
    with open('MessageStorage.txt', 'rb') as rfp:
        messages = pickle.load(rfp)

# clears all stored messages
def erase_stored_mesg():
    if os.path.getsize('MessageStorage.txt') > 0 :
        with open('MessageStorage.txt', 'rb') as rfp:
            messages = []
    with open('MessageStorage.txt', 'wb') as wfp:
        pickle.dump(messages, wfp)

#---------------------------------------GSHEETS FUNCTIONS---------------------------------------------------------------

# signs into google sheets
def signinGSheets():
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('GoogleSheetsSecrets.json', scope)
    client = gspread.authorize(creds)
    return client

# takes the designated person and action and adds it to their cell in gsheets
def addToSheets(person, action, target, target2, target3):
    client = signinGSheets()
    employee_list = getEmployeeList()
    spread = client.open('Insealation Employee Time Clock (' + strftime("%Y", gmtime()) + ')')
    sh = spread.get_worksheet(0)
    cells = sh.findall('Logan Taylor')
    if action == 'time':                                # time action
        for i in range(0, len(cells), 1):
            if cells[i].col == 3:
                if target2 == 'in':
                    input_col = 3
                    if int(target[:-3]) < 4:
                        target = target + 'PM'
                if target2 == 'out':
                    input_col = 4
                    if int(target[:-3]) < 11:
                        target = target + 'PM'
                    elif int(target[:-3]) >= 11:
                        target = target + 'PM?'
                week_day = datetime.datetime.today().weekday()
                if week_day == 3:
                    input_row = cells[i].row + 2
                if week_day == 4:
                    input_row = cells[i].row + 3
                if week_day == 5:
                    input_row = cells[i].row + 4
                if week_day == 6:
                    input_row = cells[i].row + 5
                if week_day == 0:
                    input_row = cells[i].row + 6
                if week_day == 1:
                    input_row = cells[i].row + 7
                if week_day == 2:
                    input_row = cells[i].row + 9
        sh.update_cell(input_row, input_col, target)
    if action == 'stroke':                              # stroke count action
        for i in range(0, len(cells), 1):
            if cells[i].row == 23:
                input_col = cells[i].col
                sets = sh.findall(target2)
                if len(sets) == 0:
                    if target3 == 'a':
                        for i in range(26, 33, 1):
                            if sh.cell(i, 10).value == '':
                                sh.update_cell(i, 10, target2)
                                input_row = i
                                break
                    if target3 == 'b':
                        for i in range(35, 42, 1):
                            if sh.cell(i, 10).value == '':
                                sh.update_cell(i, 10, target2)
                                input_row = i
                                break
                sets = sh.findall(target2)
                input_row = sets[0].row
                sh.update_cell(input_row, input_col, target)

# creates new weekly time clock worksheet
def newTimeSheet(date):
    client = signinGSheets()
    employee_list = getEmployeeList()
    sheet = client.open('Insealation Employee Time Clock (' + strftime("%Y", gmtime()) + ')')
    newsh = sheet.get_worksheet(0)
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

#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------MAIN ROUTE--------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)


# listens for recieved SMS
@app.route('/sms', methods=['GET', 'POST'])
def sms_recieve():
    From = request.form['From']
    Body = request.form['Body']
    message_storage(From, Body)
    sms_distribute(From, Body)
    return ''

# checks current time to activate certain events
def timeCheck():
    newTimeSheet('date')
    schedule.every().monday.at("3:00").do(newTimeSheet, strftime("%m/%d/%Y", gmtime()))     # fills this new weeks time sheet with list of current employees
    schedule.every().wednesday.at("23:00").do(send_stored_mesg)                             # sends stored messages for the week to superior
    schedule.every().thursday.at("3:00").do(erase_stored_mesg)                              # erases stored messages at the end of the week
    schedule.every().day.at('12:00').do(reminder_SMS, 'time in')                            # sends SMS to employee if they have not clocked in
    schedule.every().day.at('21:00').do(reminder_SMS, 'time out')                           # sends SMS to employee if they have not clocked out
    while True:
        schedule.run_pending()
        time.sleep(20)

if __name__ == '__main__':
    t = threading.Thread(target=timeCheck)                                                  # runs thread for scheduled events
    t.start()
    app.run(host='0.0.0.0', debug=True, use_reloader=False)                                 # listens for recieved SMS

