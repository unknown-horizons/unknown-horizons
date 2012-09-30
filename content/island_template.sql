PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE "ground" (
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"ground_id" INT NOT NULL,
	"action_id" TEXT NOT NULL,
	"rotation" INT NOT NULL
);

COMMIT;
