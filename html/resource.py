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
import cgi
from http import cookies
import json
import dbSession
import dbShared
import pymysql
import ghShared
import ghLists
import ghObjects
from jinja2 import Environment, FileSystemLoader

def getResourceHistory(conn, spawnID):
	# generate table of resource event history
	resHistory = ''
	sqlStr = 'SELECT eventTime, userID, eventType, planetName, eventDetail, galaxyName FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID LEFT JOIN tPlanet ON tResourceEvents.planetID = tPlanet.planetID LEFT JOIN tGalaxy ON tResourceEvents.galaxy = tGalaxy.galaxyID WHERE tResources.spawnID="' + str(spawnID) + '" ORDER BY eventTime DESC;'
	try:
		cursor = conn.cursor()
	except Exception:
		resHistory = '<div class="error">Error: could not connect to database</div>'

	if (cursor):
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		resHistory += '<table class="userData">'
		resHistory += '<thead><tr class="tableHead"><td>Time</td><td>User</td><td>Action</td><td width="50">Planet</td><td>Details</td><td>Galaxy</td></th></thead>'
		while (row != None):
			if row[4] == None:
				details = '-'
			else:
				details = row[4]

			resHistory += '  <tr class="statRow"><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td>'.format(str(row[0]), row[1], ghShared.getActionName(row[2]), str(row[3]), details, row[5])
			resHistory += '  </tr>'
			row = cursor.fetchone()
		resHistory += '  </table>'
		cursor.close()

	return resHistory

def getResource(conn, logged_state, currentUser, spawnID, galaxy, spawnName):
	if logged_state == 1:
		favJoin = ' LEFT JOIN (SELECT itemID, favGroup, units FROM tFavorites WHERE userID=%(currentUser)s AND favType=1) favs ON tResources.spawnID = favs.itemID'
		favCols = ', favGroup, units'
	else:
		favJoin = ''
		favCols = ', NULL, NULL'
	if spawnID != None:
		criteriaStr = 'spawnID=%(spawnID)s'
	else:
		criteriaStr = 'galaxy=%(galaxy)s AND spawnName=%(spawnName)s'

	try:
		cursor = conn.cursor()
	except Exception:
		errorstr = "Error: could not connect to database"

	if (cursor):
		sqlStr = """
			SELECT
				spawnID, spawnName, galaxy, entered, enteredBy, tResources.resourceType, rt1.resourceTypeName, rt1.resourceGroup,
				CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,
				CASE WHEN COALESCE(rto.CRmax, rt1.CRmax) > 0 THEN ((CR - COALESCE(rto.CRmin, rt1.CRmin)) / (COALESCE(rto.CRmax, rt1.CRmax) - COALESCE(rto.CRmin, rt1.CRmin)))*100 ELSE NULL END AS CRperc,
				CASE WHEN COALESCE(rto.CDmax, rt1.CDmax) > 0 THEN ((CD - COALESCE(rto.CDmin, rt1.CDmin)) / (COALESCE(rto.CDmax, rt1.CDmax) - COALESCE(rto.CDmin, rt1.CDmin)))*100 ELSE NULL END AS CDperc,
				CASE WHEN COALESCE(rto.DRmax, rt1.DRmax) > 0 THEN ((DR - COALESCE(rto.DRmin, rt1.DRmin)) / (COALESCE(rto.DRmax, rt1.DRmax) - COALESCE(rto.DRmin, rt1.DRmin)))*100 ELSE NULL END AS DRperc,
				CASE WHEN COALESCE(rto.FLmax, rt1.FLmax) > 0 THEN ((FL - COALESCE(rto.FLmin, rt1.FLmin)) / (COALESCE(rto.FLmax, rt1.FLmax) - COALESCE(rto.FLmin, rt1.FLmin)))*100 ELSE NULL END AS FLperc,
				CASE WHEN COALESCE(rto.HRmax, rt1.HRmax) > 0 THEN ((HR - COALESCE(rto.HRmin, rt1.HRmin)) / (COALESCE(rto.HRmax, rt1.HRmax) - COALESCE(rto.HRmin, rt1.HRmin)))*100 ELSE NULL END AS HRperc,
				CASE WHEN COALESCE(rto.MAmax, rt1.MAmax) > 0 THEN ((MA - COALESCE(rto.MAmin, rt1.MAmin)) / (COALESCE(rto.MAmax, rt1.MAmax) - COALESCE(rto.MAmin, rt1.MAmin)))*100 ELSE NULL END AS MAperc,
				CASE WHEN COALESCE(rto.PEmax, rt1.PEmax) > 0 THEN ((PE - COALESCE(rto.PEmin, rt1.PEmin)) / (COALESCE(rto.PEmax, rt1.PEmax) - COALESCE(rto.PEmin, rt1.PEmin)))*100 ELSE NULL END AS PEperc,
				CASE WHEN COALESCE(rto.OQmax, rt1.OQmax) > 0 THEN ((OQ - COALESCE(rto.OQmin, rt1.OQmin)) / (COALESCE(rto.OQmax, rt1.OQmax) - COALESCE(rto.OQmin, rt1.OQmin)))*100 ELSE NULL END AS OQperc,
				CASE WHEN COALESCE(rto.SRmax, rt1.SRmax) > 0 THEN ((SR - COALESCE(rto.SRmin, rt1.SRmin)) / (COALESCE(rto.SRmax, rt1.SRmax) - COALESCE(rto.SRmin, rt1.SRmin)))*100 ELSE NULL END AS SRperc,
				CASE WHEN COALESCE(rto.UTmax, rt1.UTmax) > 0 THEN ((UT - COALESCE(rto.UTmin, rt1.UTmin)) / (COALESCE(rto.UTmax, rt1.UTmax) - COALESCE(rto.UTmin, rt1.UTmin)))*100 ELSE NULL END AS UTperc,
				CASE WHEN COALESCE(rto.ERmax, rt1.ERmax) > 0 THEN ((ER - COALESCE(rto.ERmin, rt1.ERmin)) / (COALESCE(rto.ERmax, rt1.ERmax) - COALESCE(rto.ERmin, rt1.ERmin)))*100 ELSE NULL END AS ERperc,
				rt1.containerType, verified, verifiedBy, unavailable, unavailableBy, rg1.groupName, rt1.resourceCategory, rg2.groupName AS categoryName {favCols},
				(SELECT GROUP_CONCAT(resourceGroup SEPARATOR ",") FROM tResourceTypeGroup rtg WHERE rtg.resourceType=tResources.resourceType)
			FROM tResources
				INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType
				INNER JOIN tResourceGroup rg1 ON rt1.resourceGroup = rg1.resourceGroup
				INNER JOIN tResourceGroup rg2 ON rt1.resourceCategory = rg2.resourceGroup
				LEFT JOIN tResourceTypeOverrides rto ON rto.resourceType = tResources.resourceType AND rto.galaxyID = tResources.galaxy
				{favJoin}
			WHERE {criteriaStr};
		""".format(favCols=favCols, favJoin=favJoin, criteriaStr=criteriaStr)

		cursor.execute(sqlStr, {
			'currentUser': currentUser,
			'galaxy': ghShared.tryInt(galaxy),
			'spawnID': ghShared.tryInt(spawnID),
			'spawnName': spawnName
		})
		row = cursor.fetchone()

		# get resource box if the spawn was found
		if (row != None):
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
			if row[38] != None:
				s.favorite = 1
				s.favGroup = row[38]
			if row[39] != None:
				s.units = row[39]
			if row[40] != None:
				s.groupList = ',' + row[40] + ','
			s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])
		else:
			s = None

		cursor.close()

	return s

def main():
	resHTML = '<h2>That resource does not exist</h2>'
	resHistory = ''
	useCookies = 1
	linkappend = ''
	logged_state = 0
	currentUser = ''
	galaxy = ''
	spawnName = ''
	spawnID = 0
	spawnStats = ''
	spawnContainerType = ''
	spawnResourceTypeName = ''
	uiTheme = ''
	galaxyState = 0
	userReputation = 0
	admin = False
	availablePlanetIDs = []
	# Get current url
	try:
		url = os.environ['SCRIPT_NAME']
	except KeyError:
		url = ''

	form = cgi.FieldStorage()
	# Get Cookies

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
			loginResult = C['loginAttempt'].value
		except KeyError:
			loginResult = 'success'
		try:
			sid = C['gh_sid'].value
		except KeyError:
			sid = form.getfirst('gh_sid', '')
		try:
			uiTheme = C['uiTheme'].value
		except KeyError:
			uiTheme = ''
	else:
		loginResult = form.getfirst('loginAttempt', '')
		sid = form.getfirst('gh_sid', '')

	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)

	# Get a session

	if loginResult == None:
		loginResult = 'success'

	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess
		if (uiTheme == ''):
			uiTheme = dbShared.getUserAttr(currentUser, 'themeName')
		if (useCookies == 0):
			linkappend = 'gh_sid=' + sid
	else:
		if (uiTheme == ''):
			uiTheme = 'crafter'

	path = ['']
	if 'PATH_INFO' in os.environ:
		path = os.environ['PATH_INFO'].split('/')[1:]
		path = [p for p in path if p != '']

	if len(path) > 1:
		galaxy = dbShared.dbInsertSafe(path[0])
		spawnName = dbShared.dbInsertSafe(path[1])
		if galaxy != '':
			conn = dbShared.ghConn()
			spawn = getResource(conn, logged_state, currentUser, None, galaxy, spawnName)
			if spawn != None:
				spawnID = spawn.spawnID
				spawnStats = 'ER ' + str(spawn.stats.ER) + '&#xA;'
				spawnStats += 'CR ' + str(spawn.stats.CR) + '&#xA;'
				spawnStats += 'CD ' + str(spawn.stats.CD) + '&#xA;'
				spawnStats += 'DR ' + str(spawn.stats.DR) + '&#xA;'
				spawnStats += 'FL ' + str(spawn.stats.FL) + '&#xA;'
				spawnStats += 'HR ' + str(spawn.stats.HR) + '&#xA;'
				spawnStats += 'MA ' + str(spawn.stats.MA) + '&#xA;'
				spawnStats += 'PE ' + str(spawn.stats.PE) + '&#xA;'
				spawnStats += 'OQ ' + str(spawn.stats.OQ) + '&#xA;'
				spawnStats += 'SR ' + str(spawn.stats.SR) + '&#xA;'
				spawnStats += 'UT ' + str(spawn.stats.UT) + '&#xA;'
				spawnContainerType = spawn.containerType
				spawnResourceTypeName = spawn.resourceTypeName

				galaxyState = dbShared.galaxyState(spawn.spawnGalaxy)
				# Only show update tools if user logged in and has positive reputation
				stats = dbShared.getUserStats(currentUser, galaxy).split(",")
				userReputation = int(stats[2])
				admin = dbShared.getUserAdmin(conn, currentUser, galaxy)

				if logged_state > 0 and galaxyState == 1:
					controlsUser = currentUser
				else:
					controlsUser = ''

				availablePlanetIDs = [str(p.planetID) for p in spawn.planets if p.enteredBy != None]
				resHTML = spawn.getHTML(0, "", controlsUser, userReputation, admin)
				resHistory = getResourceHistory(conn, spawn.spawnID)
			conn.close()
		else:
			resHTML = '<h2>No Galaxy/Resource name given</h2>'
	else:
		resHTML = '<h2>No Galaxy/Resource name given</h2>'

	pictureName = dbShared.getUserAttr(currentUser, 'pictureName')

	print('Content-type: text/html\n')
	env = Environment(loader=FileSystemLoader('templates'))
	env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
	env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
	template = env.get_template('resource.html')
	print(template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), spawnName=spawnName, availablePlanetIDsJSON=json.dumps(availablePlanetIDs), resHTML=resHTML, resHistory=resHistory, showAdmin=(userReputation >= ghShared.MIN_REP_VALS['EDIT_RESOURCE_GALAXY_NAME'] or admin), spawnID=spawnID, spawnGalaxy=galaxy, spawnStats=spawnStats, spawnContainerType=spawnContainerType, spawnResourceTypeName=spawnResourceTypeName, enableCAPTCHA=ghShared.RECAPTCHA_ENABLED, siteidCAPTCHA=ghShared.RECAPTCHA_SITEID))


if __name__ == "__main__":
	main()
