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
def getProfOrder(profID):
	stats = {}
	weightTotal = 0
	tmpGroup = ''
	obyStr = ''
	obyStr2 = ''
	#maxCheckStr = ''
	if profID.isdigit():
		expCursor = conn.cursor()
		expCursor.execute('SELECT "holdername", statName, Sum(statWeight) AS sw, Sum(weightTotal) AS wt FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID INNER JOIN tSchematic ON tSchematicQualities.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + prof + ' GROUP BY statName;')
		expRow = expCursor.fetchone()
		while (expRow != None):
			if expRow[0] != tmpGroup:
				weightTotal += int(expRow[3])
				tmpGroup = int(expRow[3])
			if expRow[1] in stats:
				stats[expRow[1]] = stats[expRow[1]] + int(expRow[2])
			else:
				stats[expRow[1]] = int(expRow[2])
			expRow = expCursor.fetchone()

		expCursor.close()
		# calculate column sort by based on quality weights((CR-CRmin) / (CRmax-CRmin))
		for k, v in stats.items():
			weightVal = '%.2f' % (v*1.0 / weightTotal * 200)
			obyStr = obyStr + '+CASE WHEN COALESCE(rto.{0}max, rt1.{0}max) > 0 THEN (({0} - COALESCE(rto.{0}min, rt1.{0}min)) / (COALESCE(rto.{0}max, rt1.{0}max) - COALESCE(rto.{0}min, rt1.{0}min)))* {1} ELSE 0 END'.format(k, weightVal)
			obyStr2 = obyStr2 + '+CASE WHEN COALESCE(rto.{0}max, rt1.{0}max) > 0 THEN {1} ELSE 0 END'.format(k, weightVal)

		if len(obyStr)>1:
			obyStr = obyStr[1:]
		if len(obyStr2)>1:
			obyStr2 = obyStr2[1:]

		if len(obyStr) > 0 and len(obyStr2) > 0:
			return ' ((' + obyStr + ')*1000) / (' + obyStr2 + ')'
		else:
			return ' OQ'
	else:
		return ' OQ'
#
def getTypeOrder(tabID, typeID):
	stats = {}
	weightTotal = 0
	tmpGroup = ''
	obyStr = ''
	obyStr2 = ''
	if tabID.isdigit():
		sqlStr = 'SELECT "holdername", statName, Sum(statWeight) AS sw, Sum(weightTotal) AS wt FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID INNER JOIN tSchematic ON tSchematicQualities.schematicID = tSchematic.schematicID WHERE craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY statName;'
		#sys.stderr.write('typeid: ' + typeID + '\n')
		expCursor = conn.cursor()
		expCursor.execute(sqlStr)
		expRow = expCursor.fetchone()
		while (expRow != None):
			if expRow[0] != tmpGroup:
				weightTotal += int(expRow[3])
				tmpGroup = int(expRow[3])
			if expRow[1] in stats:
				stats[expRow[1]] = stats[expRow[1]] + int(expRow[2])
			else:
				stats[expRow[1]] = int(expRow[2])
			expRow = expCursor.fetchone()

		expCursor.close()
		# calculate column sort by based on quality weights
		for k, v in stats.items():
			weightVal = '%.2f' % (v / weightTotal * 200)
			obyStr += '+CASE WHEN COALESCE(rto.{0}max, rt1.{0}max) > 0 THEN (({0} - COALESCE(rto.{0}min, rt1.{0}min)) / (COALESCE(rto.{0}max, rt1.{0}max) - COALESCE(rto.{0}min, rt1.{0}min)))*{1} ELSE {1}/2 END'.format(k, weightVal)
			obyStr2 += '+' + weightVal
		if len(obyStr)>1:
			obyStr = obyStr[1:]
		if len(obyStr2)>1:
			obyStr2 = obyStr2[1:]
		return ' (' + obyStr + ') / (' + obyStr2 + ')'
	else:
		return ' OQ'

# get comma separated list of resource categories to exclude for a set of schematics
def getTypeResGroups(tabID, typeID):
	resStr = '""'
	if tabID.isdigit():
		sqlStr = '(SELECT rtg.resourceGroup FROM tResourceTypeGroup rtg INNER JOIN tSchematicIngredients ON rtg.resourceType = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID WHERE tSchematic.craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND tSchematic.objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY rtg.resourceGroup) UNION (SELECT rgc.resourceGroup FROM tResourceGroupCategory rgc INNER JOIN tSchematicIngredients ON rgc.resourceCategory = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID WHERE tSchematic.craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND tSchematic.objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY rgc.resourceGroup) UNION (SELECT rgc.resourceGroup FROM tResourceGroupCategory rgc INNER JOIN tSchematicIngredients ON rgc.resourceGroup = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID WHERE tSchematic.craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND tSchematic.objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY rgc.resourceGroup);'
		cursor = conn.cursor()
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			resStr = resStr + ',"' + row[0] + '"'
			row = cursor.fetchone()

	return resStr

# get comma separated list of resource categories to exclude for a set of schematics
def getProfResGroups(profID):
	resStr = '""'
	if profID.isdigit():
		sqlStr = '(SELECT rtg.resourceGroup FROM tResourceTypeGroup rtg INNER JOIN tSchematicIngredients ON rtg.resourceType = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + profID
		sqlStr = sqlStr + ' GROUP BY rtg.resourceGroup) UNION (SELECT rgc.resourceGroup FROM tResourceGroupCategory rgc INNER JOIN tSchematicIngredients ON rgc.resourceCategory = tSchematicIngredients.ingredientObject OR rgc.resourceGroup = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + profID
		sqlStr = sqlStr + ' GROUP BY rgc.resourceGroup);'
		cursor = conn.cursor()
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			resStr = resStr + ',"' + row[0] + '"'
			row = cursor.fetchone()

	return resStr

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
craftingTab = form.getfirst('craftingTab', '')
objectType = form.getfirst('objectType', '')
resGroup = form.getfirst('resGroup', '')
unavailable = form.getfirst('unavailable', '')
resType = form.getfirst('resType', '')
boxFormat = form.getfirst('boxFormat', '')
# Get a session
logged_state = 0
linkappend = ''
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
prof = dbShared.dbInsertSafe(prof)
resGroup = dbShared.dbInsertSafe(resGroup)
resType = dbShared.dbInsertSafe(resType)
boxFormat = dbShared.dbInsertSafe(boxFormat)

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid


# Main program

print('Content-type: text/html\n')
print('<table width="100%" class=resourceStats>')
if galaxy != '':
	galaxyState = dbShared.galaxyState(galaxy)
	conn = dbShared.ghConn()

	# Only show update tools if user logged in and has positive reputation
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")

	cursor = conn.cursor()
	orderVals = ''
	if boxFormat == '0':
		formatStyle = 0
	else:
		formatStyle = 1
	if logged_state == 1:
		favJoin = ' LEFT JOIN (SELECT itemID, favGroup, units FROM tFavorites WHERE userID=%(currentUser)s AND favType=1) favs ON tResources.spawnID = favs.itemID'
		favCols = ', favGroup, units'
	else:
		favJoin = ''
		favCols = ', NULL, NULL'

	if (cursor):
		if prof.isdigit() and prof != '0':
			# get order by profession combined schematic use
			orderVals += getProfOrder(prof)
		elif craftingTab.isdigit():
			# get order by crafting tab + object type schematic use
			orderVals += getTypeOrder(craftingTab, objectType)
		else:
			# base order on average presence of stats in all schematics of all present stats with extra modifier if an extremely high stat other than CR or ER exists
			orderVals += """
				(
				  (
				    CASE WHEN COALESCE(rto.CRmax, rt1.CRmax) > 0 THEN ((CR - COALESCE(rto.CRmin, rt1.CRmin)) / (COALESCE(rto.CRmax, rt1.CRmax) - COALESCE(rto.CRmin, rt1.CRmin)))*.06 ELSE 0 END +
				    CASE WHEN COALESCE(rto.CDmax, rt1.CDmax) > 0 THEN ((CD - COALESCE(rto.CDmin, rt1.CDmin)) / (COALESCE(rto.CDmax, rt1.CDmax) - COALESCE(rto.CDmin, rt1.CDmin)))*12.74 ELSE 0 END +
				    CASE WHEN COALESCE(rto.DRmax, rt1.DRmax) > 0 THEN ((DR - COALESCE(rto.DRmin, rt1.DRmin)) / (COALESCE(rto.DRmax, rt1.DRmax) - COALESCE(rto.DRmin, rt1.DRmin)))*12.26 ELSE 0 END +
				    CASE WHEN COALESCE(rto.FLmax, rt1.FLmax) > 0 THEN ((FL - COALESCE(rto.FLmin, rt1.FLmin)) / (COALESCE(rto.FLmax, rt1.FLmax) - COALESCE(rto.FLmin, rt1.FLmin)))*3.22 ELSE 0 END +
				    CASE WHEN COALESCE(rto.HRmax, rt1.HRmax) > 0 THEN ((HR - COALESCE(rto.HRmin, rt1.HRmin)) / (COALESCE(rto.HRmax, rt1.HRmax) - COALESCE(rto.HRmin, rt1.HRmin)))*1.27 ELSE 0 END +
				    CASE WHEN COALESCE(rto.MAmax, rt1.MAmax) > 0 THEN ((MA - COALESCE(rto.MAmin, rt1.MAmin)) / (COALESCE(rto.MAmax, rt1.MAmax) - COALESCE(rto.MAmin, rt1.MAmin)))*5.1 ELSE 0 END +
				    CASE WHEN COALESCE(rto.PEmax, rt1.PEmax) > 0 THEN ((PE - COALESCE(rto.PEmin, rt1.PEmin)) / (COALESCE(rto.PEmax, rt1.PEmax) - COALESCE(rto.PEmin, rt1.PEmin)))*9.34 ELSE 0 END +
				    CASE WHEN COALESCE(rto.OQmax, rt1.OQmax) > 0 THEN ((OQ - COALESCE(rto.OQmin, rt1.OQmin)) / (COALESCE(rto.OQmax, rt1.OQmax) - COALESCE(rto.OQmin, rt1.OQmin)))*30.64 ELSE 0 END +
				    CASE WHEN COALESCE(rto.SRmax, rt1.SRmax) > 0 THEN ((SR - COALESCE(rto.SRmin, rt1.SRmin)) / (COALESCE(rto.SRmax, rt1.SRmax) - COALESCE(rto.SRmin, rt1.SRmin)))*9.16 ELSE 0 END +
				    CASE WHEN COALESCE(rto.UTmax, rt1.UTmax) > 0 THEN ((UT - COALESCE(rto.UTmin, rt1.UTmin)) / (COALESCE(rto.UTmax, rt1.UTmax) - COALESCE(rto.UTmin, rt1.UTmin)))*16.2 ELSE 0 END
				  )
				  /
				  (
				    CASE WHEN COALESCE(rto.CRmax, rt1.CRmax) > 0 THEN .06 ELSE 0 END +
				    CASE WHEN COALESCE(rto.CDmax, rt1.CDmax) > 0 THEN 12.74 ELSE 0 END +
				    CASE WHEN COALESCE(rto.DRmax, rt1.DRmax) > 0 THEN 12.26 ELSE 0 END +
				    CASE WHEN COALESCE(rto.FLmax, rt1.FLmax) > 0 THEN 3.22 ELSE 0 END +
				    CASE WHEN COALESCE(rto.HRmax, rt1.HRmax) > 0 THEN 1.27 ELSE 0 END +
				    CASE WHEN COALESCE(rto.MAmax, rt1.MAmax) > 0 THEN 5.1 ELSE 0 END +
				    CASE WHEN COALESCE(rto.PEmax, rt1.PEmax) > 0 THEN 9.34 ELSE 0 END +
				    CASE WHEN COALESCE(rto.OQmax, rt1.OQmax) > 0 THEN 30.64 ELSE 0 END +
				    CASE WHEN COALESCE(rto.SRmax, rt1.SRmax) > 0 THEN 9.16 ELSE 0 END +
				    CASE WHEN COALESCE(rto.UTmax, rt1.UTmax) > 0 THEN 16.2 ELSE 0 END
				  )
				  *
				  1000
				  +
				  (
				    CASE WHEN GREATEST(
				      IFNULL((CD - COALESCE(rto.CDmin, rt1.CDmin)) / (COALESCE(rto.CDmax, rt1.CDmax) - COALESCE(rto.CDmin, rt1.CDmin)),0),
				      IFNULL((DR - COALESCE(rto.DRmin, rt1.DRmin)) / (COALESCE(rto.DRmax, rt1.DRmax) - COALESCE(rto.DRmin, rt1.DRmin)),0),
				      IFNULL((FL - COALESCE(rto.FLmin, rt1.FLmin)) / (COALESCE(rto.FLmax, rt1.FLmax) - COALESCE(rto.FLmin, rt1.FLmin)),0),
				      IFNULL((HR - COALESCE(rto.HRmin, rt1.HRmin)) / (COALESCE(rto.HRmax, rt1.HRmax) - COALESCE(rto.HRmin, rt1.HRmin)),0),
				      IFNULL((MA - COALESCE(rto.MAmin, rt1.MAmin)) / (COALESCE(rto.MAmax, rt1.MAmax) - COALESCE(rto.MAmin, rt1.MAmin)),0),
				      IFNULL((PE - COALESCE(rto.PEmin, rt1.PEmin)) / (COALESCE(rto.PEmax, rt1.PEmax) - COALESCE(rto.PEmin, rt1.PEmin)),0),
				      IFNULL((OQ - COALESCE(rto.OQmin, rt1.OQmin)) / (COALESCE(rto.OQmax, rt1.OQmax) - COALESCE(rto.OQmin, rt1.OQmin)),0),
				      IFNULL((SR - COALESCE(rto.SRmin, rt1.SRmin)) / (COALESCE(rto.SRmax, rt1.SRmax) - COALESCE(rto.SRmin, rt1.SRmin)),0),
				      IFNULL((UT - COALESCE(rto.UTmin, rt1.UTmin)) / (COALESCE(rto.UTmax, rt1.UTmax) - COALESCE(rto.UTmin, rt1.UTmin)),0)
				    ) > .85 THEN 5 ELSE 0 END
				  )
				  +
				  (
				    CASE WHEN GREATEST(
				      IFNULL((CD - COALESCE(rto.CDmin, rt1.CDmin)) / (COALESCE(rto.CDmax, rt1.CDmax) - COALESCE(rto.CDmin, rt1.CDmin)),0),
				      IFNULL((DR - COALESCE(rto.DRmin, rt1.DRmin)) / (COALESCE(rto.DRmax, rt1.DRmax) - COALESCE(rto.DRmin, rt1.DRmin)),0),
				      IFNULL((FL - COALESCE(rto.FLmin, rt1.FLmin)) / (COALESCE(rto.FLmax, rt1.FLmax) - COALESCE(rto.FLmin, rt1.FLmin)),0),
				      IFNULL((HR - COALESCE(rto.HRmin, rt1.HRmin)) / (COALESCE(rto.HRmax, rt1.HRmax) - COALESCE(rto.HRmin, rt1.HRmin)),0),
				      IFNULL((MA - COALESCE(rto.MAmin, rt1.MAmin)) / (COALESCE(rto.MAmax, rt1.MAmax) - COALESCE(rto.MAmin, rt1.MAmin)),0),
				      IFNULL((PE - COALESCE(rto.PEmin, rt1.PEmin)) / (COALESCE(rto.PEmax, rt1.PEmax) - COALESCE(rto.PEmin, rt1.PEmin)),0),
				      IFNULL((OQ - COALESCE(rto.OQmin, rt1.OQmin)) / (COALESCE(rto.OQmax, rt1.OQmax) - COALESCE(rto.OQmin, rt1.OQmin)),0),
				      IFNULL((SR - COALESCE(rto.SRmin, rt1.SRmin)) / (COALESCE(rto.SRmax, rt1.SRmax) - COALESCE(rto.SRmin, rt1.SRmin)),0),
				      IFNULL((UT - COALESCE(rto.UTmin, rt1.UTmin)) / (COALESCE(rto.UTmax, rt1.UTmax) - COALESCE(rto.UTmin, rt1.UTmin)),0)
				    ) > .98 THEN 20 ELSE 0 END
				  )
				)
			"""

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
				containerType, {orderVals}, verified, verifiedBy, unavailable, unavailableBy {favCols}
			FROM tResources
				INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType
				 LEFT JOIN tResourceTypeOverrides rto ON rto.resourceType = tResources.resourceType AND rto.galaxyID = tResources.galaxy
				{favJoin}
		"""

		if (resGroup != 'any' and resGroup != ''):
			sqlStr1 += ' INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup=%(resGroup)s GROUP BY resourceType) rtg ON tResources.resourceType = rtg.resourceType'

		if unavailable == "1":
			sqlStr1 += ' WHERE tResources.galaxy=%(galaxy)s'
		else:
			sqlStr1 += ' WHERE tResources.galaxy=%(galaxy)s AND unavailable IS NULL'

		if (resType != 'any' and resType != ''):
			sqlStr1 += ' AND tResources.resourceType = %(resType)s'

		if prof.isdigit() and prof != '0':
			sqlStr1 += ' AND rt1.resourceGroup IN (' + getProfResGroups(prof) + ')'

		if craftingTab.isdigit():
			sqlStr1 += ' AND rt1.resourceGroup IN (' + getTypeResGroups(craftingTab, objectType) + ')'

		sqlStr1 += ' ORDER BY {orderVals}'
		sqlStr1 += ' DESC LIMIT 6;'
		#sys.stderr.write(sqlStr1)

		cursor.execute(
			sqlStr1.format(orderVals=orderVals, favCols=favCols, favJoin=favJoin),
			{'currentUser': currentUser, 'galaxy': ghShared.tryInt(galaxy), 'resGroup': resGroup, 'resType': resType}
		)

		row = cursor.fetchone()
		while (row != None):
			# populate spawn object and print
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

			s.overallScore = row[31]
			s.entered = row[3]
			s.enteredBy = row[4]
			s.verified = row[32]
			s.verifiedBy = row[33]
			s.unavailable = row[34]
			s.unavailableBy = row[35]
			if row[36] != None:
				s.favorite = 1
				s.favGroup = row[36]
			if row[37] != None:
				s.units = row[37]
			s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])

			print('  <tr><td>')
			if logged_state > 0 and galaxyState == 1:
				controlsUser = currentUser
			else:
				controlsUser = ''
			print(s.getHTML(formatStyle, "", controlsUser, int(stats[2]), dbShared.getUserAdmin(conn, currentUser, galaxy)))
			print('</td></tr>')
			row = cursor.fetchone()

		cursor.close()
	conn.close()
print('  </table>')
