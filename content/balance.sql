CREATE TABLE "animals" (
	"building_id" INT NOT NULL,
	"unit_id" INT NOT NULL,
	"count" INT NOT NULL
);
INSERT INTO "animals" VALUES(18, 1000003, 3);

CREATE TABLE "unit_production" (
	"production_line" INT NOT NULL,
	"unit" INT NOT NULL,
	"amount" INT NOT NULL
);
INSERT INTO "unit_production" VALUES(15, 1000001, 1);
INSERT INTO "unit_production" VALUES(58, 1000020, 1);
INSERT INTO "unit_production" VALUES(62, 1000016, 1);
INSERT INTO "unit_production" VALUES(63, 1000016, 1);
INSERT INTO "unit_production" VALUES(64, 1000016, 1);
INSERT INTO "unit_production" VALUES(68, 1000016, 1);

CREATE TABLE "start_resources" (
	"resource" INT,
	"amount" INT
);
INSERT INTO "start_resources" VALUES(4, 30);
INSERT INTO "start_resources" VALUES(5, 30);
INSERT INTO "start_resources" VALUES(6, 30);
INSERT INTO "start_resources" VALUES(40, 12);

CREATE TABLE "player_start_res" (
	"resource" INT NOT NULL,
	"amount" INT NOT NULL
);
INSERT INTO "player_start_res" VALUES(1, 30000);

CREATE TABLE "storage_building_capacity" (
	"type" INT,
	"size" INT
);
INSERT INTO "storage_building_capacity" VALUES(1, 30);
INSERT INTO "storage_building_capacity" VALUES(2, 10);
INSERT INTO "storage_building_capacity" VALUES(4, 0);

CREATE TABLE "balance_values" (
	"name" TEXT,
	"value" REAL
);
INSERT INTO "balance_values" VALUES('happiness_init_value', 50.0);
INSERT INTO "balance_values" VALUES('happiness_min_value', 0.0);
INSERT INTO "balance_values" VALUES('happiness_max_value', 100.0);
INSERT INTO "balance_values" VALUES('happiness_inhabitants_increase_requirement', 70.0);
INSERT INTO "balance_values" VALUES('happiness_inhabitants_decrease_limit', 30.0);
INSERT INTO "balance_values" VALUES('happiness_level_up_requirement', 80.0);
INSERT INTO "balance_values" VALUES('happiness_level_down_limit', 10.0);
