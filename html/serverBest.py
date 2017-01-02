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
import MySQLdb
import dbShared
import optparse

# Return position among server best
def getPosition(conn, spawnID, galaxy, statWeights, resourceGroup):
    obyStr = ''
    obyStr2 = ''
    maxCheckStr = ''

    # calculate column sort by based on quality weights
    for k, v in statWeights.iteritems():
        weightVal = '%.2f' % v
        obyStr = ''.join((obyStr, '+CASE WHEN ', k, 'max > 0 THEN (', k, ' / 1000)*', weightVal, ' ELSE ', weightVal, '*.25 END'))
        obyStr2 = ''.join((obyStr2, '+', weightVal))
        maxCheckStr = ''.join((maxCheckStr, '+', k, 'max'))

    #sys.stderr.write(' (' + obyStr + ') / (' + obyStr2 + ')\n')
    if (obyStr != ''):
        obyStr = obyStr[1:]
        obyStr2 = obyStr2[1:]
        maxCheckStr = maxCheckStr[1:]
    else:
        # No stat weights to calculate
        return 0

    sqlStr1 = ''.join(('SELECT spawnID, (', obyStr, ') / (', obyStr2, ') AS overallScore, ', maxCheckStr, ' FROM tResources INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType',
              ' INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup="', resourceGroup, '" OR resourceType="', resourceGroup, '" GROUP BY resourceType) rtg ON tResources.resourceType = rtg.resourceType'
              ' WHERE galaxy=', str(galaxy), ' ORDER BY (', obyStr, ') / (' + obyStr2 + ')'
              ' DESC LIMIT 8;'))
    cursor = conn.cursor()

    spawnPos = 0
    if (cursor):
        cursor.execute(sqlStr1)
        row = cursor.fetchone()
        # Check is spawn in top 3 or within 5% quality of 1st
        rowPos = 1
        topScore = 0.0
        while row != None and row[1] != None:
            if rowPos == 1:
                topScore = row[1]
            if row[1] / topScore < .95:
                break
            if str(row[0]) == spawnID and row[2] != 0:
                spawnPos = rowPos
                break

            rowPos += 1
            row = cursor.fetchone()

        cursor.close()

    return spawnPos

def checkSchematics(conn, spawnID, galaxy, prof, resourceTypes):
    bestPositions = {}
    # Select schematics where ingredient in type or groups of type
    sqlStr2 = 'SELECT tSchematic.schematicID, ingredientObject, Sum(ingredientContribution), schematicName, resName FROM tSchematicIngredients INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup  LEFT JOIN (SELECT resourceGroup AS resID, groupName AS resName FROM tResourceGroup UNION ALL SELECT resourceType, resourceTypeName FROM tResourceType) res ON ingredientObject = res.resID WHERE profID=' + str(prof) + ' AND ingredientObject IN (' + str(resourceTypes) + ') GROUP BY tSchematic.schematicID, ingredientObject ORDER BY tSchematic.schematicID, ingredientQuantity DESC, ingredientName;'
    ingCursor = conn.cursor()
    ingCursor.execute(sqlStr2)
    ingRow = ingCursor.fetchone()
    # Iterate over ingredients of matching schematics
    while ingRow != None:
        # get quality attributes for schematic
        stats = {}
        lastStats = {}
        tmpGroup = ''
        spawnPosition = 0
        # Select the quality groups for this ingredient
        expSQL = 'SELECT expGroup, statName, Sum(statWeight)/Sum(weightTotal)*100 AS wp FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID WHERE schematicID="' + ingRow[0] + '" GROUP BY expGroup, statName;'
        expCursor = conn.cursor()
        expCursor.execute(expSQL)
        expRow = expCursor.fetchone()
        while (expRow != None):
            if expRow[0] != tmpGroup:
                if tmpGroup != '':
                    # Check for top 3 status
                    if stats != lastStats:
                        spawnPosition = getPosition(conn, spawnID, galaxy, stats, ingRow[1])
                    if spawnPosition > 0:
                        if spawnPosition == 1:
                            eventDetail = ''.join(('New server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
                        else:
                            eventDetail = ''.join(('Almost server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
                        eventDetail = dbShared.dbInsertSafe(eventDetail)
                        if ingRow[0] in bestPositions:
                            bestPositions[ingRow[0]].append(eventDetail)
                        else:
                            bestPositions[ingRow[0]] = [eventDetail]
                        dbShared.logSchematicEvent(spawnID, galaxy, ingRow[0], tmpGroup, str(spawnPosition), eventDetail)
                    lastStats = stats
                    stats = {}
                tmpGroup = expRow[0]
            if expRow[1] in stats:
                stats[expRow[1]] = stats[expRow[1]] + float(expRow[2])
            else:
                stats[expRow[1]] = float(expRow[2])
            expRow = expCursor.fetchone()

        # Check for top 3 status on last ingredient
        if stats != lastStats:
            spawnPosition = getPosition(conn, spawnID, galaxy, stats, ingRow[1])
        if spawnPosition > 0:
            if spawnPosition == 1:
                eventDetail = ''.join(('New server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
            else:
                eventDetail = ''.join(('Almost server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
            eventDetail = dbShared.dbInsertSafe(eventDetail)
            if ingRow[0] in bestPositions:
                bestPositions[ingRow[0]].append(eventDetail)
            else:
                bestPositions[ingRow[0]] = [eventDetail]
            dbShared.logSchematicEvent(spawnID, galaxy, ingRow[0], tmpGroup, str(spawnPosition), eventDetail)
        expCursor.close()

        ingRow = ingCursor.fetchone()
    ingCursor.close()

    return bestPositions

def checkSpawn(spawnID):
    # Look up additional spawn info needed
    professions = []
    profresults = []
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute('SELECT galaxy, resourceType, (SELECT GROUP_CONCAT(resourceGroup SEPARATOR "\',\'") FROM tResourceTypeGroup rtg WHERE rtg.resourceType=tResources.resourceType) FROM tResources WHERE spawnID=%s;', spawnID)
    row = cursor.fetchone()
    if row != None:
        # Check each profession separately but ignore ones that do not care about quality
        pc = conn.cursor()
        pc.execute('SELECT profID, profName FROM tProfession WHERE craftingQuality > 0;')
        pcRow = pc.fetchone()
        while pcRow != None:
            result = checkSchematics(conn, str(spawnID), row[0], pcRow[0], "".join(("'", row[1], "','", str(row[2]), "'")))
            if result != None and len(result) > 0:
                professions.append(str(pcRow[0]))
                profresults.append(result)

            pcRow = pc.fetchone()
    else:
        sys.stderr.write('Could not find that spawn.')
    cursor.close()
    conn.close()

    return [professions, profresults]

def main():
    # get the spawn id we are checking
    parser = optparse.OptionParser()
    parser.add_option('-s', '--spawn', dest='spawn')
    (opts, args) = parser.parse_args()
    if opts.spawn is None:
	    sys.stderr.write("missing required options.\n")
	    exit(-1)
    else:
        print checkSpawn(opts.spawn)

if __name__ == "__main__":
    main()
