'''
hedgeit.common.sendmail

Contains:
    sendmail()
'''

import smtplib
from email.mime.text import MIMEText

def sendmail(toaddr, subject, body):
    msg = MIMEText(body)
            
    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = subject
    fromaddr = 'wilki2021@gmail.com'
    msg['From'] = fromaddr
    msg['To'] = toaddr

    username = 'wilki2021@gmail.com'
    password = 'soarhead'
           
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()
