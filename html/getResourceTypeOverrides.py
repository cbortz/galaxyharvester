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

import dbShared
import cgi
import pymysql
import json

form = cgi.FieldStorage()

# Get form info
galaxy = form.getfirst("galaxy", "")
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)

if galaxy.isdigit():
	galaxy = int(galaxy)
	overrides = []

	overridesSql = """
		SELECT
			rto.resourceType,
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
			rto.ERmax,
			CONCAT(
				"p",
				CASE WHEN rt1.CRmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.CDmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.DRmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.FLmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.HRmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.MAmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.PEmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.OQmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.SRmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.UTmax > 0 THEN "1" ELSE "0" END,
				CASE WHEN rt1.ERmax > 0 THEN "1" ELSE "0" END
			) AS statMask
		FROM
			tResourceTypeOverrides rto
			INNER JOIN tResourceType rt1 ON rt1.resourceType = rto.resourceType
		WHERE
			rto.galaxyID = %(galaxyID)s;
	"""

	conn = dbShared.ghConn()
	cursor = conn.cursor(pymysql.cursors.DictCursor)
	cursor.execute(overridesSql, {'galaxyID': galaxy})
	row = cursor.fetchone()

	while row != None:
		overrides.append(row)
		row = cursor.fetchone()

	result = {'overrides': overrides}
	status = 200

else:
	result = {'message': 'Galaxy ID must be an integer'}
	status = 400

print(f'Status: {status}')
print('Content-Type: application/json\n')
print(json.dumps(result))

# """
#   <table id="">
#     <thead>
#       <tr>
#         <td></td>
#         <td>ER</td>
#         <td>CR</td>
#         <td>CD</td>
#         <td>DR</td>
#         <td>FL</td>
#         <td>HR</td>
#         <td>MA</td>
#         <td>PE</td>
#         <td>OQ</td>
#         <td>SR</td>
#         <td>UT</td>
#       </tr>
#     </thead>
#     <tbody>
#       <tr>
#         <td>Min</td>
#         <td><input type="text" size="5" maxlength="4" value="{ERmin}" id="ERmin{idx}" name="ERmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{CRmin}" id="CRmin{idx}" name="CRmin{idx}"></td>
#         <td><input type="text" size="5" maxlength="4" value="{CDmin}" id="CDmin{idx}" name="CDmin{idx}"></td>
#         <td><input type="text" size="5" maxlength="4" value="{DRmin}" id="DRmin{idx}" name="DRmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{FLmin}" id="FLmin{idx}" name="FLmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{HRmin}" id="HRmin{idx}" name="HRmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{MAmin}" id="MAmin{idx}" name="MAmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{PEmin}" id="PEmin{idx}" name="PEmin{idx}"></td>
#         <td><input type="text" size="5" maxlength="4" value="{OQmin}" id="OQmin{idx}" name="OQmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{SRmin}" id="SRmin{idx}" name="SRmin{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{UTmin}" id="UTmin{idx}" name="UTmin{idx}" disabled="disabled"></td>
#       </tr>
#       <tr>
#         <td>Max</td>
#         <td><input type="text" size="5" maxlength="4" value="{ERmax}" id="ERmax{idx}" name="ERmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{CRmax}" id="CRmax{idx}" name="CRmax{idx}"></td>
#         <td><input type="text" size="5" maxlength="4" value="{CDmax}" id="CDmax{idx}" name="CDmax{idx}"></td>
#         <td><input type="text" size="5" maxlength="4" value="{DRmax}" id="DRmax{idx}" name="DRmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{FLmax}" id="FLmax{idx}" name="FLmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{HRmax}" id="HRmax{idx}" name="HRmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{MAmax}" id="MAmax{idx}" name="MAmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{PEmax}" id="PEmax{idx}" name="PEmax{idx}"></td>
#         <td><input type="text" size="5" maxlength="4" value="{OQmax}" id="OQmax{idx}" name="OQmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{SRmax}" id="SRmax{idx}" name="SRmax{idx}" disabled="disabled"></td>
#         <td><input type="text" size="5" maxlength="4" value="{UTmax}" id="UTmax{idx}" name="UTmax{idx}" disabled="disabled"></td>
#       </tr>
#     </tbody>
#   </table>
# """
