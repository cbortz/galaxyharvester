use swgresource;

CREATE TABLE `tResourceTypeOverrides` (
  `galaxyID` int(11) NOT NULL,
  `resourceType` varchar(63) NOT NULL,
  `CRmin` smallint(6) DEFAULT NULL,
  `CRmax` smallint(6) DEFAULT NULL,
  `CDmin` smallint(6) DEFAULT NULL,
  `CDmax` smallint(6) DEFAULT NULL,
  `DRmin` smallint(6) DEFAULT NULL,
  `DRmax` smallint(6) DEFAULT NULL,
  `FLmin` smallint(6) DEFAULT NULL,
  `FLmax` smallint(6) DEFAULT NULL,
  `HRmin` smallint(6) DEFAULT NULL,
  `HRmax` smallint(6) DEFAULT NULL,
  `MAmin` smallint(6) DEFAULT NULL,
  `MAmax` smallint(6) DEFAULT NULL,
  `PEmin` smallint(6) DEFAULT NULL,
  `PEmax` smallint(6) DEFAULT NULL,
  `OQmin` smallint(6) DEFAULT NULL,
  `OQmax` smallint(6) DEFAULT NULL,
  `SRmin` smallint(6) DEFAULT NULL,
  `SRmax` smallint(6) DEFAULT NULL,
  `UTmin` smallint(6) DEFAULT NULL,
  `UTmax` smallint(6) DEFAULT NULL,
  `ERmin` smallint(6) DEFAULT NULL,
  `ERmax` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`galaxyID`,`resourceType`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
