import smtplib
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import pickle


def send_stored_mesg():
    with open('/home/pi/Desktop/EliteTimeClock/MessageStorage.txt', 'rb') as rfp:
        messages = pickle.load(rfp)
    text = ''
    for i in range(0, len(messages), 1):
        text = text + '\n\n' + messages[i]
    print(text) 
    server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
    server.starttls()
    server.login("loganrt11@yahoo.com", "River2017")
    server.sendmail("loganrt11@yahoo.com", "eliteinsealation@gmail.com", text.encode('utf8'))
    server.quit()


if __name__ == '__main__':
    send_stored_mesg()
