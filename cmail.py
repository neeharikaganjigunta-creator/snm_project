app_password="eqyp cjip hqta lcpa"
import smtplib
from email.message import EmailMessage    # EmailMesssage is a class which is used to define email format
def send_mail(to,subject,body):
    server=smtplib.SMTP_SSL("smtp.gmail.com",465)    # server -> object, 465 -> port number 
    server.login("neeharikaganjigunta@gmail.com",app_password)   
    msg=EmailMessage()   # obj for EmailMessage
    msg["FROM"]="neeharikaganjigunta@gmail.com"   # FROM -> attribute
    msg["SUBJECT"]=subject   # defined in function
    msg["TO"]=to   # defined in function
    msg.set_content(body)   # method
    server.send_message(msg)   # send_message -> method
    server.close()   # closing server object (optional)