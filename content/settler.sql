CREATE TABLE settler_production_line(level INTEGER, production_line INTEGER);
INSERT INTO "settler_production_line" VALUES(0,19);
INSERT INTO "settler_production_line" VALUES(0,21);
INSERT INTO "settler_production_line" VALUES(1,19);
INSERT INTO "settler_production_line" VALUES(1,20);
INSERT INTO "settler_production_line" VALUES(1,21);
INSERT INTO "settler_production_line" VALUES(1,26);
INSERT INTO "settler_production_line" VALUES(0,30);
INSERT INTO "settler_production_line" VALUES(1,30);
INSERT INTO "settler_production_line" VALUES(2,30);
INSERT INTO "settler_production_line" VALUES(2,43);
INSERT INTO "settler_production_line" VALUES(2,20);
INSERT INTO "settler_production_line" VALUES(2,21);
INSERT INTO "settler_production_line" VALUES(2,44);
INSERT INTO "settler_production_line" VALUES(2,41);
INSERT INTO "settler_production_line" VALUES(2,69);
INSERT INTO "settler_production_line" VALUES(2,70);
CREATE TABLE upgrade_material(level INT NOT NULL, production_line INT NOT NULL);
INSERT INTO "upgrade_material" VALUES(1,24);
INSERT INTO "upgrade_material" VALUES(2,35);
CREATE TABLE balance_values(name TEXT, value FLOAT);
INSERT INTO "balance_values" VALUES('happiness_init_value',50.0);
INSERT INTO "balance_values" VALUES('happiness_min_value',0.0);
INSERT INTO "balance_values" VALUES('happiness_max_value',100.0);
INSERT INTO "balance_values" VALUES('happiness_inhabitants_increase_requirement',70.0);
INSERT INTO "balance_values" VALUES('happiness_inhabitants_decrease_limit',30.0);
INSERT INTO "balance_values" VALUES('happiness_level_up_requirement',80.0);
INSERT INTO "balance_values" VALUES('happiness_level_down_limit',10.0);
CREATE TABLE settler_level (
    "level" INT NOT NULL DEFAULT (''),
    "name" TEXT NOT NULL DEFAULT (''),
    "tax_income" INT NOT NULL DEFAULT (''),
    "inhabitants_max" INT
, "residential_name" TEXT   DEFAULT (''));
INSERT INTO "settler_level" VALUES(0,'sailor',2,2,'tent');
INSERT INTO "settler_level" VALUES(1,'pioneer',3,3,'hut');
INSERT INTO "settler_level" VALUES(2,'settler',6,5,'house');
INSERT INTO "settler_level" VALUES(3,'citizen',10,8,'stone house');
INSERT INTO "settler_level" VALUES(4,'merchant',15,13,'estate');
INSERT INTO "settler_level" VALUES(5,'aristocrat',25,21,'manor');
