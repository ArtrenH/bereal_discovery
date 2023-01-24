import time
def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1


import datetime
def print_time():
    dt = datetime.datetime.now()
    print(dt.strftime('[%Y.%m.%d | %H:%M:%S]'))

if __name__ == "__main__":
    print_time()