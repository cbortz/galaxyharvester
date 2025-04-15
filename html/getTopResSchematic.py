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
import ghLists
import ghObjects
#

def getResourceSQL(maxCheckStr, favCols, joinStr, galaxy, resGroup, obyStr, obyStr2, mine):
	sqlStr1 = """
		SELECT
			spawnID, spawnName, tResources.galaxy, entered, enteredBy, tResources.resourceType, resourceTypeName, resourceGroup,
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
			containerType, verified, verifiedBy, unavailable, unavailableBy,
			{maxCheckStr} {favCols}, ({obyStr}) / ({obyStr2}) AS overallScore
		FROM tResources
			INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType
			LEFT JOIN tResourceTypeOverrides rto ON rto.resourceType = tResources.resourceType AND rto.galaxyID = tResources.galaxy
			{joinStr}
	"""

	if (resGroup != 'any' and resGroup != ''):
		sqlStr1 += ' INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup="{resGroup}" OR resourceType="{resGroup}" GROUP BY resourceType) rtg ON tResources.resourceType = rtg.resourceType'

	if unavailable == '1' or mine != '':
		sqlStr1 += ' WHERE tResources.galaxy={galaxy}'
	else:
		sqlStr1 += ' WHERE tResources.galaxy={galaxy} AND unavailable IS NULL'

	if mine != '':
		sqlStr1 += " AND favGroup IS NOT NULL AND favGroup NOT IN ('Surveying', 'Shopping')"

	if obyStr != '':
		sqlStr1 += ' ORDER BY ({obyStr}) / ({obyStr2}) DESC LIMIT 3'

	sqlStr1 += ';'

	return sqlStr1.format(
		favCols=favCols,
		galaxy=galaxy,
		joinStr=joinStr,
		maxCheckStr=maxCheckStr,
		obyStr2=obyStr2,
		obyStr=obyStr,
		resGroup=resGroup
	)

def getResourceData(conn, resSQL, logged_state, galaxyState, resourceFormat, reputation, statsMatter):
	# get resource data for given criteria
	resourceHTML = '<table width="100%" class=resourceStats>'
	cursor = conn.cursor()

	if (cursor):
		cursor.execute(resSQL)
		row = cursor.fetchone()
		# check first row to see if all quality stats do not belong to resource type
		if (row != None):
			# print resource rows if stats matter
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
				if row[36] != None:
					s.favorite = 1
					s.favGroup = row[36]
				if row[37] != None:
					s.units = row[37]
				if row[38] != None:
					s.overallScore = row[38]*1000
				s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])

				resourceHTML += '  <tr><td>'
				if logged_state > 0 and galaxyState == 1:
					controlsUser = currentUser
				else:
					controlsUser = ''
				resourceHTML += s.getHTML(resourceFormat, "", controlsUser, reputation, dbShared.getUserAdmin(conn, currentUser, galaxy), statsMatter)
				resourceHTML += '  </td></tr>'
				row = cursor.fetchone()
		else:
			resourceHTML += '<tr><td>Not Available</td></tr>'
		cursor.close()
	resourceHTML += '</table>'
	return resourceHTML

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

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
		loginResult = C['loginAttempt'].value
	except KeyError:
		loginResult = 'success'
	try:
		sid = C['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	sid = form.getfirst('gh_sid', '')

galaxy = form.getfirst('galaxy', '')
prof = form.getfirst('prof', '')
schematicID = form.getfirst('schematicID', '')
unavailable = form.getfirst('unavailable', '')
excludeGroups = form.getfirst('excludeGroups', '')
compare = form.getfirst('compare','undefined')

# Get a session
logged_state = 0
linkappend = ''
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
prof = dbShared.dbInsertSafe(prof)
schematicID = dbShared.dbInsertSafe(schematicID)
excludeGroups = dbShared.dbInsertSafe(excludeGroups)

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid


# Main program
resGroup = ''
errstr = ''
joinStr = ''
galaxyState = 0

if (schematicID == ''):
	errstr = errstr + "You must specify a schematic to get resource information for. \r\n"
if (galaxy == ''):
	errstr = errstr + "No Galaxy Specified. \r\n"
else:
	galaxyState = dbShared.galaxyState(galaxy)

if logged_state == 1:
	joinStr = joinStr + ' LEFT JOIN (SELECT itemID, favGroup, units FROM tFavorites WHERE userID="' + currentUser + '" AND favType=1) favs ON tResources.spawnID = favs.itemID'
	favCols = ', favGroup, units'
else:
	favCols = ', NULL, NULL'

print('Content-type: text/html\n')
if (errstr != ''):
	print(errstr)
else:
	conn = dbShared.ghConn()
	# Only show update tools if user logged in and has positive reputation
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])

	# first get list of non-component ingredients
	ingCursor = conn.cursor()
	if (ingCursor):
		ingSQL = 'SELECT res.resID, Max(res.resName) FROM tSchematicIngredients LEFT JOIN (SELECT resourceGroup AS resID, groupName AS resName FROM tResourceGroup UNION ALL SELECT resourceType, resourceTypeName FROM tResourceType) res ON ingredientObject = res.resID WHERE schematicID="' + schematicID + '" AND ingredientType=0 GROUP BY res.resID;'
		ingCursor.execute(ingSQL)
		ingRow = ingCursor.fetchone()
		while (ingRow != None):
			if (resGroup != str(ingRow[0])):
				resGroup = str(ingRow[0])
				print('<h3 class="standOut">' + str(ingRow[1]) + '</h3>')

			# get quality attributes for schematic
			stats = {}
			weightTotal = 0
			tmpGroup = ''
			obyStr = ''
			obyStr2 = ''
			maxCheckStr = ''
			expSQL = 'SELECT expGroup, statName, Sum(statWeight) AS sw, Sum(weightTotal) AS wt FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID WHERE schematicID="' + schematicID + '"'
			if len(excludeGroups) > 0:
				expSQL = expSQL + ' AND expGroup NOT IN (' + excludeGroups + ')'
			expSQL = expSQL + ' GROUP BY expGroup, statName;'
			expCursor = conn.cursor()
			expCursor.execute(expSQL)
			expRow = expCursor.fetchone()
			while (expRow != None):
				if expRow[0] != tmpGroup:
					weightTotal += float(expRow[3])
					tmpGroup = float(expRow[3])
				if expRow[1] in stats:
					stats[expRow[1]] = stats[expRow[1]] + float(expRow[2])
				else:
					stats[expRow[1]] = float(expRow[2])
				expRow = expCursor.fetchone()

			expCursor.close()
			# calculate column sort by based on quality weights
			for k, v in stats.items():
				weightVal = '%.2f' % (v / weightTotal * 200)
				obyStr += '+CASE WHEN COALESCE(rto.{0}max, rt1.{0}max) > 0 THEN ({0} / 1000)*{1} ELSE {1} *.25 END'.format(k, weightVal)
				obyStr2 += '+' + weightVal
				maxCheckStr += '+COALESCE(rto.{0}max, rt1.{0}max)'.format(k)
			#sys.stderr.write(' (' + obyStr + ') / (' + obyStr2 + ')\n')
			if (obyStr != ''):
				obyStr = obyStr[1:]
				obyStr2 = obyStr2[1:]
				maxCheckStr = maxCheckStr[1:]
				statsMatter = True
			else:
				obyStr = '1'
				obyStr2 = '1'
				maxCheckStr = '1'
				statsMatter = False

			if compare == 'undefined' or logged_state == 0:
				resourceFormat = 0
				resSQL = getResourceSQL(maxCheckStr, favCols, joinStr, galaxy, resGroup, obyStr, obyStr2, '')
				print(getResourceData(conn, resSQL, logged_state, galaxyState, resourceFormat, userReputation, statsMatter))
			else:
				# Include side by side comparison of inventory
				resourceFormat = 1
				print('<div class="resourceCompareGroup">')
				print('<div class="inlineBlock" style="width:50%">')
				print('<h4>Galaxy</h4>')
				resSQL = getResourceSQL(maxCheckStr, favCols, joinStr, galaxy, resGroup, obyStr, obyStr2, '')
				print(getResourceData(conn, resSQL, logged_state, galaxyState, resourceFormat, userReputation, statsMatter))
				print('</div><div class="inlineBlock" style="width:50%">')
				print('<h4>My Inventory</h4>')
				resSQL = getResourceSQL(maxCheckStr, favCols, joinStr, galaxy, resGroup, obyStr, obyStr2, 'y')
				print(getResourceData(conn, resSQL, logged_state, galaxyState, resourceFormat, userReputation, statsMatter))
				print('</div></div>')
			ingRow = ingCursor.fetchone()
		ingCursor.close()
	conn.close()
