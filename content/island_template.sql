PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE "island_properties" (
	"name" TEXT NOT NULL,
	"value" TEXT NOT NULL
);

CREATE TABLE "ground" (
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"ground_id" INT NOT NULL,
	"action_id" TEXT NOT NULL,
	"rotation" INT NOT NULL
);

COMMIT;
