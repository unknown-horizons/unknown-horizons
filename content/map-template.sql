CREATE TABLE "ground" (
	"island_id" INT NOT NULL,
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"ground_id" INT NOT NULL,
	"action_id" TEXT NOT NULL,
	"rotation" INT NOT NULL
);

CREATE TABLE properties (
	"name" TEXT NOT NULL,
	"value" TEXT NOT NULL
);
