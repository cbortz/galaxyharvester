#!/usr/bin/env python3
"""

 Copyright 2021 Paul Willworth <ioscode@gmail.com>

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

import os
import sys
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
import ghShared
import ghLists
import ghObjects
#

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
C = cookies.SimpleCookie()
try:
	C.load(os.environ['HTTP_COOKIE'])
except KeyError:
	errorstr = 'no cookies\n'

if errorstr == '':
	try:
		currentUser = C['userID'].value
	except KeyError:
		currentUser = ''
	try:
		sid = C['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	sid = form.getfirst('gh_sid', '')

# Get a session
logged_state = 0
galaxy = form.getfirst('galaxy', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

# Main program

print('Content-type: text/html\n')
print('<table width="100%" class=resourceStats>')
if galaxy != '':
	if logged_state == 1:
		favJoin = 'LEFT JOIN (SELECT itemID, favGroup, units FROM tFavorites WHERE userID= %(currentUser)s AND favType=1) favs ON tResources.spawnID = favs.itemID'
		favCols = ', favGroup, units'
	else:
		favJoin = ''
		favCols = ', NULL, NULL'
	galaxyState = dbShared.galaxyState(galaxy)
	conn = dbShared.ghConn()

	# Only show update tools if user logged in and has positive reputation
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])

	cursor = conn.cursor()
	if (cursor):
		sqlStr = """
			SELECT
				spawnID, spawnName, galaxy, entered, enteredBy, tResources.resourceType, resourceTypeName, resourceGroup,
				CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,
				CASE WHEN COALESCE(rto.CRmax, rt1.CRmax) > 0 THEN (((CASE WHEN CR IS NULL THEN 0 ELSE CR END) - COALESCE(rto.CRmin, rt1.CRmin)) / (COALESCE(rto.CRmax, rt1.CRmax) - COALESCE(rto.CRmin, rt1.CRmin)))*100 ELSE NULL END AS CRperc,
				CASE WHEN COALESCE(rto.CDmax, rt1.CDmax) > 0 THEN (((CASE WHEN CD IS NULL THEN 0 ELSE CD END) - COALESCE(rto.CDmin, rt1.CDmin)) / (COALESCE(rto.CDmax, rt1.CDmax) - COALESCE(rto.CDmin, rt1.CDmin)))*100 ELSE NULL END AS CDperc,
				CASE WHEN COALESCE(rto.DRmax, rt1.DRmax) > 0 THEN (((CASE WHEN DR IS NULL THEN 0 ELSE DR END) - COALESCE(rto.DRmin, rt1.DRmin)) / (COALESCE(rto.DRmax, rt1.DRmax) - COALESCE(rto.DRmin, rt1.DRmin)))*100 ELSE NULL END AS DRperc,
				CASE WHEN COALESCE(rto.FLmax, rt1.FLmax) > 0 THEN (((CASE WHEN FL IS NULL THEN 0 ELSE FL END) - COALESCE(rto.FLmin, rt1.FLmin)) / (COALESCE(rto.FLmax, rt1.FLmax) - COALESCE(rto.FLmin, rt1.FLmin)))*100 ELSE NULL END AS FLperc,
				CASE WHEN COALESCE(rto.HRmax, rt1.HRmax) > 0 THEN (((CASE WHEN HR IS NULL THEN 0 ELSE HR END) - COALESCE(rto.HRmin, rt1.HRmin)) / (COALESCE(rto.HRmax, rt1.HRmax) - COALESCE(rto.HRmin, rt1.HRmin)))*100 ELSE NULL END AS HRperc,
				CASE WHEN COALESCE(rto.MAmax, rt1.MAmax) > 0 THEN (((CASE WHEN MA IS NULL THEN 0 ELSE MA END) - COALESCE(rto.MAmin, rt1.MAmin)) / (COALESCE(rto.MAmax, rt1.MAmax) - COALESCE(rto.MAmin, rt1.MAmin)))*100 ELSE NULL END AS MAperc,
				CASE WHEN COALESCE(rto.PEmax, rt1.PEmax) > 0 THEN (((CASE WHEN PE IS NULL THEN 0 ELSE PE END) - COALESCE(rto.PEmin, rt1.PEmin)) / (COALESCE(rto.PEmax, rt1.PEmax) - COALESCE(rto.PEmin, rt1.PEmin)))*100 ELSE NULL END AS PEperc,
				CASE WHEN COALESCE(rto.OQmax, rt1.OQmax) > 0 THEN (((CASE WHEN OQ IS NULL THEN 0 ELSE OQ END) - COALESCE(rto.OQmin, rt1.OQmin)) / (CASE WHEN COALESCE(rto.OQmax, rt1.OQmax) - COALESCE(rto.OQmin, rt1.OQmin) < 1 THEN 1 ELSE COALESCE(rto.OQmax, rt1.OQmax) - COALESCE(rto.OQmin, rt1.OQmin) END))*100 ELSE NULL END AS OQperc,
				CASE WHEN COALESCE(rto.SRmax, rt1.SRmax) > 0 THEN (((CASE WHEN SR IS NULL THEN 0 ELSE SR END) - COALESCE(rto.SRmin, rt1.SRmin)) / (COALESCE(rto.SRmax, rt1.SRmax) - COALESCE(rto.SRmin, rt1.SRmin)))*100 ELSE NULL END AS SRperc,
				CASE WHEN COALESCE(rto.UTmax, rt1.UTmax) > 0 THEN (((CASE WHEN UT IS NULL THEN 0 ELSE UT END) - COALESCE(rto.UTmin, rt1.UTmin)) / (COALESCE(rto.UTmax, rt1.UTmax) - COALESCE(rto.UTmin, rt1.UTmin)))*100 ELSE NULL END AS UTperc,
				CASE WHEN COALESCE(rto.ERmax, rt1.ERmax) > 0 THEN (((CASE WHEN ER IS NULL THEN 0 ELSE ER END) - COALESCE(rto.ERmin, rt1.ERmin)) / (COALESCE(rto.ERmax, rt1.ERmax) - COALESCE(rto.ERmin, rt1.ERmin)))*100 ELSE NULL END AS ERperc,
				containerType, verified, verifiedBy, unavailable, unavailableBy{favCols}
			FROM tResources
				INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType
				LEFT JOIN tResourceTypeOverrides rto ON rto.resourceType = tResources.resourceType AND rto.galaxyID = tResources.galaxy
				{favJoin}
			WHERE galaxy = %(galaxy)s AND unavailable IS NULL
			ORDER BY entered DESC LIMIT 5;
		""".format(favCols=favCols, favJoin=favJoin)

		cursor.execute(sqlStr, {'galaxy': ghShared.tryInt(galaxy), 'currentUser': currentUser})
		row = cursor.fetchone()
		while (row != None):
			s = ghObjects.resourceSpawn()
			s.spawnID = row[0]
			s.spawnName = row[1]
			s.spawnGalaxy = row[2]
			s.resourceType = row[5]
			s.resourceTypeName = row[6]
			s.containerType = row[30]
			s.stats.CR = row[8]
			s.stats.CD = row[9]
			s.stats.DR = row[10]
			s.stats.FL = row[11]
			s.stats.HR = row[12]
			s.stats.MA = row[13]
			s.stats.PE = row[14]
			s.stats.OQ = row[15]
			s.stats.SR = row[16]
			s.stats.UT = row[17]
			s.stats.ER = row[18]

			s.percentStats.CR = row[19]
			s.percentStats.CD = row[20]
			s.percentStats.DR = row[21]
			s.percentStats.FL = row[22]
			s.percentStats.HR = row[23]
			s.percentStats.MA = row[24]
			s.percentStats.PE = row[25]
			s.percentStats.OQ = row[26]
			s.percentStats.SR = row[27]
			s.percentStats.UT = row[28]
			s.percentStats.ER = row[29]

			s.entered = row[3]
			s.enteredBy = row[4]
			s.verified = row[31]
			s.verifiedBy = row[32]
			s.unavailable = row[33]
			s.unavailableBy = row[34]
			if row[35] != None:
				s.favorite = 1
				s.favGroup = row[35]
			if row[36] != None:
				s.units = row[36]
			s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])

			print('  <tr><td>')
			if logged_state > 0 and galaxyState == 1:
				controlsUser = currentUser
			else:
				controlsUser = ''
			print(s.getHTML(1, "", controlsUser, userReputation, dbShared.getUserAdmin(conn, currentUser, galaxy)))
			print('</td></tr>')
			row = cursor.fetchone()

		cursor.close()
	conn.close()
print('  </table>')
