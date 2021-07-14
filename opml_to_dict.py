import re
import os


with open("/home/robbie/Downloads/feedbro-subscriptions-20210713-141449.opml",'r') as f:
    for line in f:
        if 'title' in line:
            if len(line.split('"')) > 3:
                print("'" + line.split('"')[3] + "' : ",end='')
            else:
                continue
        if 'xmlUrl' in line:
            pid = line.split('"')[1].split('%')[-1][2:]
            print("'"+pid+"',")
