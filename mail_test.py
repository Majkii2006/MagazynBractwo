import smtplib
from email.mime.text import MIMEText

myEmail = 'magazynzdhbractwo@gmail.com'
smtp_server = 'smtp.gmail.com'
smtp_port = 587

msg = MIMEText('This email was sent from Python')
msg['Subject'] = 'The subject of the email...'
msg['From'] = myEmail
msg['To'] = myEmail

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(myEmail, 'jmbeginrxugatvjc')

server.send_message(msg)
server.quit()
