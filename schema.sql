DROP TABLE IF EXISTS emails;
CREATE TABLE emails (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  emails string NOT NULL,
  pwd    string NOT NULL,
  vpnpwd string,
  used  INTEGER DEFAULT 0
);
        	 
