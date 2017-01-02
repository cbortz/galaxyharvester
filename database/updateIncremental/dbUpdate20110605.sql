use swgresource;
CREATE TABLE tFilters (userID VARCHAR(31), galaxy SMALLINT, rowOrder SMALLINT, fltType SMALLINT, fltValue VARCHAR(63), alertTypes SMALLINT, CRmin SMALLINT, CDmin SMALLINT, DRmin SMALLINT, FLmin SMALLINT, HRmin SMALLINT, MAmin SMALLINT, PEmin SMALLINT, OQmin SMALLINT, SRmin SMALLINT, UTmin SMALLINT, ERmin SMALLINT, PRIMARY KEY (userID, galaxy, rowOrder, fltType, fltValue), INDEX IX_filter_galaxy_type_value (galaxy, fltType, fltValue));
CREATE TABLE tAlerts (alertID INT AUTO_INCREMENT PRIMARY KEY, userID VARCHAR(31), alertType SMALLINT, alertTime DATETIME, alertMessage VARCHAR(1023), alertLink VARCHAR(255), alertStatus CHAR(1), statusChanged DATETIME, INDEX IX_alerts_userid_type (userID, alertType));
