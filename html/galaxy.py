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
import cgi
from http import cookies
import dbSession
import dbShared
import pymysql
import ghShared
import ghLists
from jinja2 import Environment, FileSystemLoader


# Get extra planets for a galaxy or the available ones they can add
def getPlanetList(conn, galaxy, available):
	listHTML = ''
	if not galaxy.isdigit():
		galaxy = 0
	if available > 0:
		planetSQL = 'SELECT planetID, planetName FROM tPlanet WHERE planetID > 10 AND planetID NOT IN (SELECT planetID FROM tGalaxyPlanet WHERE galaxyID={0}) ORDER BY planetName;'.format(galaxy)
	else:
		planetSQL = 'SELECT tGalaxyPlanet.planetID, planetName FROM tGalaxyPlanet INNER JOIN tPlanet ON tGalaxyPlanet.planetID=tPlanet.planetID WHERE tGalaxyPlanet.planetID > 10 AND tGalaxyPlanet.galaxyID={0} ORDER BY planetName;'.format(galaxy)
	cursor = conn.cursor()
	cursor.execute(planetSQL)
	row = cursor.fetchone()
	while row != None:
		listHTML += '<option value="{0}">{1}</option>'.format(row[0], row[1])
		row = cursor.fetchone()
	cursor.close()
	return listHTML

# Get extra resource types for a galaxy or the available ones they can add
def getElectiveResourceTypeList(conn, galaxy, available):
	listHTML = ''
	if not galaxy.isdigit():
		galaxy = 0

	is_or_is_not_null = "IS NULL" if available > 0 else "IS NOT NULL"

	resourceTypeSQL = """
		SELECT
			tResourceType.resourceType,
			resourceTypeName
		FROM tResourceType
			LEFT JOIN tGalaxyResourceType tgrt ON tgrt.resourceType = tResourceType.resourceType AND tgrt.galaxyID = %(galaxy)s
		WHERE
			elective = 1 AND tgrt.resourceType {0}
		ORDER BY resourceTypeName;
	""".format(is_or_is_not_null)

	cursor = conn.cursor()
	cursor.execute(resourceTypeSQL, {'galaxy': ghShared.tryInt(galaxy)})
	row = cursor.fetchone()
	while row != None:
		listHTML += '<option value="{0}">{1}</option>'.format(row[0], row[1])
		row = cursor.fetchone()
	cursor.close()
	return listHTML

def getResourceTypeOverridesHTML(conn, galaxy):
	listHTML = ''
	overrides = getResourceTypeOverrides(conn, galaxy)

	for idx, override in enumerate(overrides):
		listHTML += resourceTypeOverideHTML(override, idx)

	return listHTML

def getResourceTypeOverrides(conn, galaxy):
	overrides = []

	if not galaxy.isdigit():
		return overrides

	overridesSql = """
		SELECT
			rto.resourceType,
			rt1.resourceTypeName,
			rto.CRmin,
			rto.CRmax,
			rto.CDmin,
			rto.CDmax,
			rto.DRmin,
			rto.DRmax,
			rto.FLmin,
			rto.FLmax,
			rto.HRmin,
			rto.HRmax,
			rto.MAmin,
			rto.MAmax,
			rto.PEmin,
			rto.PEmax,
			rto.OQmin,
			rto.OQmax,
			rto.SRmin,
			rto.SRmax,
			rto.UTmin,
			rto.UTmax,
			rto.ERmin,
			rto.ERmax
		FROM tResourceTypeOverrides rto
		INNER JOIN tResourceType rt1 ON rt1.resourceType = rto.resourceType
		WHERE galaxyID = %(galaxyID)s;
	""".format()

	cursor = conn.cursor(pymysql.cursors.DictCursor)
	cursor.execute(overridesSql, {'galaxyID': ghShared.tryInt(galaxy)})
	row = cursor.fetchone()

	while row != None:
		overrides.append(row)
		row = cursor.fetchone()

	# sys.stderr.write(str(overrides))

	return overrides

def resourceTypeOverideHTML(override={}, idx='#'):
	return """
    <table id="">
      <thead>
        <tr>
          <td></td>
          <td>ER</td>
          <td>CR</td>
          <td>CD</td>
          <td>DR</td>
          <td>FL</td>
          <td>HR</td>
          <td>MA</td>
          <td>PE</td>
          <td>OQ</td>
          <td>SR</td>
          <td>UT</td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Min</td>
          <td><input type="text" size="5" maxlength="4" value="{ERmin}" id="ERmin{idx}" name="ERmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{CRmin}" id="CRmin{idx}" name="CRmin{idx}"></td>
          <td><input type="text" size="5" maxlength="4" value="{CDmin}" id="CDmin{idx}" name="CDmin{idx}"></td>
          <td><input type="text" size="5" maxlength="4" value="{DRmin}" id="DRmin{idx}" name="DRmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{FLmin}" id="FLmin{idx}" name="FLmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{HRmin}" id="HRmin{idx}" name="HRmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{MAmin}" id="MAmin{idx}" name="MAmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{PEmin}" id="PEmin{idx}" name="PEmin{idx}"></td>
          <td><input type="text" size="5" maxlength="4" value="{OQmin}" id="OQmin{idx}" name="OQmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{SRmin}" id="SRmin{idx}" name="SRmin{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{UTmin}" id="UTmin{idx}" name="UTmin{idx}" disabled="disabled"></td>
        </tr>
        <tr>
          <td>Max</td>
          <td><input type="text" size="5" maxlength="4" value="{ERmax}" id="ERmax{idx}" name="ERmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{CRmax}" id="CRmax{idx}" name="CRmax{idx}"></td>
          <td><input type="text" size="5" maxlength="4" value="{CDmax}" id="CDmax{idx}" name="CDmax{idx}"></td>
          <td><input type="text" size="5" maxlength="4" value="{DRmax}" id="DRmax{idx}" name="DRmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{FLmax}" id="FLmax{idx}" name="FLmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{HRmax}" id="HRmax{idx}" name="HRmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{MAmax}" id="MAmax{idx}" name="MAmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{PEmax}" id="PEmax{idx}" name="PEmax{idx}"></td>
          <td><input type="text" size="5" maxlength="4" value="{OQmax}" id="OQmax{idx}" name="OQmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{SRmax}" id="SRmax{idx}" name="SRmax{idx}" disabled="disabled"></td>
          <td><input type="text" size="5" maxlength="4" value="{UTmax}" id="UTmax{idx}" name="UTmax{idx}" disabled="disabled"></td>
        </tr>
      </tbody>
    </table>
	""".format(
		idx=idx,
		CDmax=override.get('CDmax') or '',
		CDmin=override.get('CDmin') or '',
		CRmax=override.get('CRmax') or '',
		CRmin=override.get('CRmin') or '',
		DRmax=override.get('DRmax') or '',
		DRmin=override.get('DRmin') or '',
		ERmax=override.get('ERmax') or '',
		ERmin=override.get('ERmin') or '',
		FLmax=override.get('FLmax') or '',
		FLmin=override.get('FLmin') or '',
		HRmax=override.get('HRmax') or '',
		HRmin=override.get('HRmin') or '',
		MAmax=override.get('MAmax') or '',
		MAmin=override.get('MAmin') or '',
		OQmax=override.get('OQmax') or '',
		OQmin=override.get('OQmin') or '',
		PEmax=override.get('PEmax') or '',
		PEmin=override.get('PEmin') or '',
		SRmax=override.get('SRmax') or '',
		SRmin=override.get('SRmin') or '',
		UTmax=override.get('UTmax') or '',
		UTmin=override.get('UTmin') or ''
	)

def main():
	useCookies = 1
	linkappend = ''
	logged_state = 0
	currentUser = ''
	msgHTML = ''
	galaxy = ''
	uiTheme = ''
	galaxyName = ''
	galaxyState = 0
	galaxyCheckedNGE = ''
	galaxyWebsite = ''
	galaxyAdminList = []
	galaxyPlanetList = []
	availablePlanetList = []
	galaxyResourceTypeList = []
	availableResourceTypeList = []
	resourceTypeOverrides = []
	galaxyAdmins = []
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

	if len(path) > 0:
		galaxy = dbShared.dbInsertSafe(path[0])
		conn = dbShared.ghConn()
		galaxyAdminList = dbShared.getGalaxyAdminList(conn, currentUser)
		if galaxy.isdigit():
			# get the galaxy details for edit
			galaxyCursor = conn.cursor()
			galaxyCursor.execute('SELECT galaxyName, galaxyState, galaxyNGE, website FROM tGalaxy WHERE galaxyID={0};'.format(galaxy))
			galaxyRow = galaxyCursor.fetchone()
			if galaxyRow != None:
				galaxyName = galaxyRow[0]
				galaxyState = galaxyRow[1]
				if galaxyRow[2] > 0:
					galaxyCheckedNGE = 'checked'
				galaxyWebsite = galaxyRow[3]
			galaxyCursor.close()
			galaxyPlanetList = getPlanetList(conn, galaxy, 0)
			availablePlanetList = getPlanetList(conn, galaxy, 1)
			availableResourceTypeList = getElectiveResourceTypeList(conn, galaxy, 1)
			galaxyResourceTypeList = getElectiveResourceTypeList(conn, galaxy, 0)
			resourceTypeOverridesHTML = getResourceTypeOverridesHTML(conn, galaxy)
			resourceTypeOverrideHTMLTemplate = resourceTypeOverideHTML()
			galaxyAdmins = dbShared.getGalaxyAdmins(conn, galaxy)
			conn.close()
		else:
			galaxyAdmins = [currentUser]
			msgHTML = '<h2>Please enter galaxy details for review.</h2>'
	else:
		msgHTML = '<h2>No Galaxy found in URL path.</h2>'

	pictureName = dbShared.getUserAttr(currentUser, 'pictureName')
	print('Content-type: text/html\n')
	env = Environment(loader=FileSystemLoader('templates'))
	env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
	env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
	template = env.get_template('galaxy.html')
	print(template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, pictureName=pictureName, loginResult=loginResult, linkappend=linkappend, url=url, imgNum=ghShared.imgNum, galaxyID=galaxy, galaxyList=ghLists.getGalaxyList(), msgHTML=msgHTML, galaxyName=galaxyName, galaxyState=galaxyState, galaxyCheckedNGE=galaxyCheckedNGE, galaxyWebsite=galaxyWebsite, galaxyStatusList=ghLists.getGalaxyStatusList(), galaxyPlanetList=galaxyPlanetList, availablePlanetList=availablePlanetList, galaxyResourceTypeList=galaxyResourceTypeList, availableResourceTypeList=availableResourceTypeList, resourceTypeOverridesHTML=resourceTypeOverridesHTML, resourceTypeOverrideHTMLTemplate=resourceTypeOverrideHTMLTemplate, galaxyAdminList=galaxyAdminList, galaxyAdmins=galaxyAdmins, enableCAPTCHA=ghShared.RECAPTCHA_ENABLED, siteidCAPTCHA=ghShared.RECAPTCHA_SITEID))


if __name__ == "__main__":
	main()
