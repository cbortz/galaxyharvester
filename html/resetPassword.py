#!/usr/bin/python
"""

 Copyright 2016 Paul Willworth <ioscode@gmail.com>

 This file is part of Galaxy Harvester.

 Galaxy Harvester is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Galaxy Harvester is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Galaxy Harvester.  If not, see <http://www.gnu.org/licenses/>.

"""

import sys
import os
import cgi
import hashlib
import MySQLdb
import dbSession
import dbShared
import ghShared
import logging
from random import *
import string
sys.path.append("../")
import dbInfo
import mailer
import mailInfo


form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
email = form.getfirst("email")
# escape input to prevent sql injection
email = dbShared.dbInsertSafe(email)

chars = string.ascii_letters + string.digits
def randomString():
    return "".join(choice(chars) for x in range(randint(6,10)))


#  Check for errors
result='';
if (email == None):
    result = "no e-mail address sent\n"
else:
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute("SELECT userID, lastReset FROM tUsers WHERE emailAddress='" + email + "';")
    row = cursor.fetchone()
    if row == None:
        result = "no account with that e-mail"
    else:
        uname = row[0]
        lastReset = row[1]

        newPass = randomString()
        crypt_pass = hashlib.sha1(dbInfo.DB_KEY3 + newPass).hexdigest()

        if (lastReset == None or ghShared.timeAgo(lastReset).find("minute") == -1):
            message = mailer.Message()
            message.From = "admin@galaxyharvester.net"
            message.To = email
            message.Subject = "Galaxy Harvester password reset"
            message.Body = "Hello " + uname + ",\n\nYour password for galaxyharvester.net has been reset to:\n\n" + newPass + "\n\n go to http://galaxyharvester.net to login.\n"
            mailer = mailer.Mailer(mailInfo.MAIL_HOST)
            mailer.login(mailInfo.MAIL_USER, mailInfo.MAIL_PASS)
            mailer.send(message)
            cursor.execute('UPDATE tUsers SET userPassword="' + crypt_pass + '", lastReset=NOW() WHERE userID="' + uname + '";')
            result = 'email sent'
        else:
            result = 'You can only reset your password 1 time per hour.'


    cursor.close()
    conn.close()


print "Content-Type: text/html\n"
print result
