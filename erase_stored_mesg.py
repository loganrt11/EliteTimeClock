import os
import pickle

def erase_stored_mesg():
    print(os.path.getsize('/home/pi/Desktop/EliteTimeClock/MessageStorage.txt'))
    if os.path.getsize('/home/pi/Desktop/EliteTimeClock/MessageStorage.txt') > 0 :
        with open('/home/pi/Desktop/EliteTimeClock/MessageStorage.txt', 'rb') as rfp:
            messages = []
        with open('/home/pi/Desktop/EliteTimeClock/MessageStorage.txt', 'wb') as wfp:
            pickle.dump(messages, wfp)
    print(os.path.getsize('/home/pi/Desktop/EliteTimeClock/MessageStorage.txt'))


if __name__ == '__main__':
    erase_stored_mesg()

