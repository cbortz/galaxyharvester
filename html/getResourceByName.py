#!/usr/bin/env python3
"""

 Copyright 2020 Paul Willworth <ioscode@gmail.com>

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
from xml.dom import minidom
import time
from datetime import datetime
#

def main():
	form = cgi.FieldStorage()
	# Get Cookies
	useCookies = 1
	C = cookies.SimpleCookie()
	try:
		C.load(os.environ['HTTP_COOKIE'])
	except KeyError:
		useCookies = 0

	if useCookies:
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
	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess

	spawnName = form.getfirst('name', '')
	galaxy = form.getfirst('galaxy', '')
	# escape input to prevent sql injection
	spawnName = dbShared.dbInsertSafe(spawnName)
	galaxy = dbShared.dbInsertSafe(galaxy)

	return getSpawnXML(spawnName, galaxy, currentUser, logged_state)


def getSpawnXML(spawnName, galaxy, currentUser, logged_state):
	RES_STATS = ['CR','CD','DR','FL','HR','MA','PE','OQ','SR','UT','ER']
	joinStr = ''
	doc = minidom.Document()
	eRoot = doc.createElement("result")
	doc.appendChild(eRoot)

	eName = doc.createElement("spawnName")
	tName = doc.createTextNode(spawnName)
	eName.appendChild(tName)
	eRoot.appendChild(eName)

	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if logged_state == 1:
		joinStr += 'LEFT JOIN (SELECT itemID, favGroup, despawnAlert FROM tFavorites WHERE userID=%(currentUser)s AND favType=1) favs ON tResources.spawnID = favs.itemID'
		favCols = ', favGroup, despawnAlert'
	else:
		favCols = ', NULL, NULL'

	if (cursor):
		spawnSQL = """
			SELECT
				spawnID, tResources.resourceType, resourceTypeName, CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,
				COALESCE(rto.CRmin, rt1.CRmin) AS CRmin,
				COALESCE(rto.CDmin, rt1.CDmin) AS CDmin,
				COALESCE(rto.DRmin, rt1.DRmin) AS DRmin,
				COALESCE(rto.FLmin, rt1.FLmin) AS FLmin,
				COALESCE(rto.HRmin, rt1.HRmin) AS HRmin,
				COALESCE(rto.MAmin, rt1.MAmin) AS MAmin,
				COALESCE(rto.PEmin, rt1.PEmin) AS PEmin,
				COALESCE(rto.OQmin, rt1.OQmin) AS OQmin,
				COALESCE(rto.SRmin, rt1.SRmin) AS SRmin,
				COALESCE(rto.UTmin, rt1.UTmin) AS UTmin,
				COALESCE(rto.ERmin, rt1.ERmin) AS ERmin,
				COALESCE(rto.CRmax, rt1.CRmax) AS CRmax,
				COALESCE(rto.CDmax, rt1.CDmax) AS CDmax,
				COALESCE(rto.DRmax, rt1.DRmax) AS DRmax,
				COALESCE(rto.FLmax, rt1.FLmax) AS FLmax,
				COALESCE(rto.HRmax, rt1.HRmax) AS HRmax,
				COALESCE(rto.MAmax, rt1.MAmax) AS MAmax,
				COALESCE(rto.PEmax, rt1.PEmax) AS PEmax,
				COALESCE(rto.OQmax, rt1.OQmax) AS OQmax,
				COALESCE(rto.SRmax, rt1.SRmax) AS SRmax,
				COALESCE(rto.UTmax, rt1.UTmax) AS UTmax,
				COALESCE(rto.ERmax, rt1.ERmax) AS ERmax,
				containerType, entered, enteredBy, unavailable, unavailableBy, verified, verifiedBy,
				(SELECT Max(concentration) FROM tWaypoint WHERE tWaypoint.spawnID=tResources.spawnID AND shareLevel=256) AS wpMaxConc{favCols}
			FROM tResources
				INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType
				LEFT JOIN tResourceTypeOverrides rto ON tResources.resourceType = rto.resourceType AND tResources.galaxy = rto.galaxyID
				{joinStr}
			WHERE galaxy= %(galaxy)s AND spawnName = %(spawnName)s;
		""".format(favCols=favCols, joinStr=joinStr)

		cursor.execute(spawnSQL, {'galaxy': ghShared.tryInt(galaxy), 'spawnName': spawnName, 'currentUser': currentUser})
		row = cursor.fetchone()

		if (row != None):
			spawnID = str(row[0])

			eSpawn = doc.createElement("spawnID")
			tSpawn = doc.createTextNode(spawnID)
			eSpawn.appendChild(tSpawn)
			eRoot.appendChild(eSpawn)

			eType = doc.createElement("resourceType")
			tType = doc.createTextNode(row[1])
			eType.appendChild(tType)
			eRoot.appendChild(eType)

			eTypeName = doc.createElement("resourceTypeName")
			tTypeName = doc.createTextNode(row[2])
			eTypeName.appendChild(tTypeName)
			eRoot.appendChild(eTypeName)

			for i in range(len(RES_STATS)):
				e = doc.createElement(RES_STATS[i])
				t = doc.createTextNode(str(row[i+3]))
				e.appendChild(t)
				eRoot.appendChild(e)

				emin = doc.createElement(RES_STATS[i] + "min")
				tmin = doc.createTextNode(str(row[i+14]))
				emin.appendChild(tmin)
				eRoot.appendChild(emin)

				emax = doc.createElement(RES_STATS[i] + "max")
				tmax = doc.createTextNode(str(row[i+25]))
				emax.appendChild(tmax)
				eRoot.appendChild(emax)

			eContainer = doc.createElement("containerType")
			tContainer = doc.createTextNode(str(row[36]))
			eContainer.appendChild(tContainer)
			eRoot.appendChild(eContainer)

			eentered = doc.createElement("entered")
			tentered = doc.createTextNode(str(row[37]))
			eentered.appendChild(tentered)
			eRoot.appendChild(eentered)

			eenteredBy = doc.createElement("enteredBy")
			tenteredBy = doc.createTextNode(str(row[38]))
			eenteredBy.appendChild(tenteredBy)
			eRoot.appendChild(eenteredBy)

			if row[39] != None:
				eunavailable = doc.createElement("unavailable")
				tunavailable = doc.createTextNode(row[39].strftime("%Y-%m-%d %H:%M:%S"))
				eunavailable.appendChild(tunavailable)
				eRoot.appendChild(eunavailable)

				eunavailableBy = doc.createElement("unavailableBy")
				tunavailableBy = doc.createTextNode(str(row[40]))
				eunavailableBy.appendChild(tunavailableBy)
				eRoot.appendChild(eunavailableBy)

			if row[41] != None:
				everified = doc.createElement("verified")
				tverified = doc.createTextNode(row[41].strftime("%Y-%m-%d %H:%M:%S"))
				everified.appendChild(tverified)
				eRoot.appendChild(everified)

				everifiedBy = doc.createElement("verifiedBy")
				tverifiedBy = doc.createTextNode(str(row[42]))
				everifiedBy.appendChild(tverifiedBy)
				eRoot.appendChild(everifiedBy)

			if row[43] != None:
				emaxWaypointConc = doc.createElement("maxWaypointConc")
				tmaxWaypointConc = doc.createTextNode(str(row[43]))
				emaxWaypointConc.appendChild(tmaxWaypointConc)
				eRoot.appendChild(emaxWaypointConc)

			if row[44] != None:
				group = row[44]
				if group == "":
					group = "default"
				efavGroup = doc.createElement("favoriteGroup")
				tfavGroup = doc.createTextNode(group)
				efavGroup.appendChild(tfavGroup)
				eRoot.appendChild(efavGroup)

				edespawnAlert = doc.createElement("despawnAlert")
				tdespawnAlert = doc.createTextNode(str(row[45]))
				edespawnAlert.appendChild(tdespawnAlert)
				eRoot.appendChild(edespawnAlert)

			planetsSQL = ''.join(('SELECT tResourcePlanet.planetID, planetName, entered, enteredBy FROM tResourcePlanet INNER JOIN tPlanet ON tResourcePlanet.planetID=tPlanet.planetID WHERE spawnID="', spawnID, '";'))
			cursor.execute(planetsSQL)
			row = cursor.fetchone()
			planets = ""
			planetNames = ""
			while (row != None):
				ePlanet = doc.createElement("planet")
				ePlanet.setAttribute("id", str(row[0]))
				ePlanet.setAttribute("entered", row[2].strftime("%Y-%m-%d %H:%M:%S"))
				ePlanet.setAttribute("enteredBy", str(row[3]))
				tPlanet = doc.createTextNode(row[1])
				ePlanet.appendChild(tPlanet)
				eRoot.appendChild(ePlanet)

				planets = planets + str(row[0]) + ","
				planetNames = planetNames + row[1] + ", "
				row = cursor.fetchone()

			if (len(planetNames) > 0):
				planetNames = planetNames[0:len(planetNames)-2]

			ePlanets = doc.createElement("Planets")
			tPlanets = doc.createTextNode(planetNames)
			ePlanets.appendChild(tPlanets)
			eRoot.appendChild(ePlanets)

			result = "found"
		else:
			result = "new"
		cursor.close()
		conn.close()
	else:
		result = "Error: could not connect to database"

	eText = doc.createElement("resultText")
	tText = doc.createTextNode(result)
	eText.appendChild(tText)
	eRoot.appendChild(eText)

	eNow = doc.createElement("serverTime")
	tNow = doc.createTextNode(datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S"))
	eNow.appendChild(tNow)
	eRoot.appendChild(eNow)

	print(doc.toxml())
	return result


print('Content-type: text/xml\n')
result = main()

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
