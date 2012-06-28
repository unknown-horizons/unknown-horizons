CREATE TABLE "colors" (
	"name" TEXT NOT NULL,
	"red" INT NOT NULL,
	"green" INT NOT NULL,
	"blue" INT NOT NULL,
	"alpha" INT NOT NULL DEFAULT 255,
	"id" INT NOT NULL
);
INSERT INTO "colors" VALUES('red',     255,  10,  10, 255,  1);
INSERT INTO "colors" VALUES('blue',      0,  72, 181, 255,  2);
INSERT INTO "colors" VALUES('green',     0, 160,  23, 255,  3);
INSERT INTO "colors" VALUES('orange',  224, 102,   0, 255,  4);
INSERT INTO "colors" VALUES('purple',  128,   0, 128, 255,  5);
INSERT INTO "colors" VALUES('cyan',      0, 255, 255, 255,  6);
INSERT INTO "colors" VALUES('yellow',  255, 215,   0, 255,  7);
INSERT INTO "colors" VALUES('pink',    255,   0, 255, 255,  8);
INSERT INTO "colors" VALUES('teal',      0, 146, 139, 255,  9);
INSERT INTO "colors" VALUES('lemon',     0, 255,   0, 255, 10);
INSERT INTO "colors" VALUES('bordeaux',150,   6,  40, 255, 11);
INSERT INTO "colors" VALUES('white',   255, 255, 255, 255, 12);
INSERT INTO "colors" VALUES('gray',    128, 128, 128, 255, 13);
INSERT INTO "colors" VALUES('black',     0,   0,   0, 255, 14);

CREATE TABLE "ground_class" (
	"ground" INT NOT NULL,
	"class" TEXT NOT NULL
);
INSERT INTO "ground_class" VALUES(1, 'coastline');
INSERT INTO "ground_class" VALUES(3, 'constructible');
INSERT INTO "ground_class" VALUES(4, 'constructible');
INSERT INTO "ground_class" VALUES(6, 'constructible');
INSERT INTO "ground_class" VALUES(5, 'coastline');
INSERT INTO "ground_class" VALUES(7, 'constructible');

CREATE TABLE "unit" (
	"id" INT NOT NULL,
	"name" TEXT NOT NULL,
	"class_package" TEXT NOT NULL,
	"class_type" TEXT NOT NULL,
	"base_velocity" REAL DEFAULT '12.0',
	"radius" INT DEFAULT '5'
);
INSERT INTO "unit" VALUES(1000001, 'Huker', 'ship', 'Ship', 5.0, 5);
INSERT INTO "unit" VALUES(1000002, 'BuildingCollector', 'collectors', 'BuildingCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000003, 'Sheep', 'animal', 'FarmAnimal', 12.0, 3);
INSERT INTO "unit" VALUES(1000004, 'Fisher', 'ship', 'FisherShip', 12.0, 5);
INSERT INTO "unit" VALUES(1000005, 'Pirate Ship', 'ship', 'PirateShip', 12.0, 5);
INSERT INTO "unit" VALUES(1000006, 'Trader', 'ship', 'TradeShip', 12.0, 8);
INSERT INTO "unit" VALUES(1000007, 'AnimalCarriage', 'collectors', 'AnimalCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000008, 'StorageCollector', 'collectors', 'StorageCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000009, 'FieldCollector', 'collectors', 'FieldCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000010, 'LumberjackCollector', 'collectors', 'FieldCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000011, 'SettlerCollector', 'collectors', 'StorageCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000013, 'Deer', 'animal', 'WildAnimal', 12.0, 5);
INSERT INTO "unit" VALUES(1000014, 'HunterCollector', 'collectors', 'HunterCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000015, 'FarmAnimalCollector', 'collectors', 'FarmAnimalCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000016, 'UsableFisher', 'ship', 'Ship', 12.0, 5);
INSERT INTO "unit" VALUES(1000017, 'Cattle', 'animal', 'FarmAnimal', 12.0, 3);
INSERT INTO "unit" VALUES(1000018, 'Boar', 'animal', 'FarmAnimal', 12.0, 5);
INSERT INTO "unit" VALUES(1000019, 'Doctor', 'collectors', 'DisasterRecoveryCollector', 12.0, 5);
INSERT INTO "unit" VALUES(1000020, 'Frigate', 'fightingship', 'FightingShip', 12.0, 5);
INSERT INTO "unit" VALUES(1000021, 'BomberMan', 'groundunit', 'FightingGroundUnit', 10.0, 5);
INSERT INTO "unit" VALUES(1000022, 'Firefighter', 'collectors', 'DisasterRecoveryCollector', 12.0, 5);

CREATE TABLE "speech" (
	"group_id" INT NOT NULL DEFAULT 0,
	"file" TEXT NOT NULL
);
INSERT INTO "speech" VALUES(1, 'content/audio/voice/map_creation/en/0.ogg');
INSERT INTO "speech" VALUES(1, 'content/audio/voice/map_creation/en/1.ogg');
INSERT INTO "speech" VALUES(1, 'content/audio/voice/map_creation/en/2.ogg');
INSERT INTO "speech" VALUES(1, 'content/audio/voice/map_creation/en/3.ogg');
INSERT INTO "speech" VALUES(2, 'content/audio/sounds/events/new_settlement.ogg');
INSERT INTO "speech" VALUES(3, 'content/audio/sounds/events/new_era.ogg');

CREATE TABLE "sounds" (
	"id" NOT NULL,
	"file" TEXT NOT NULL
);
INSERT INTO "sounds" VALUES( 1, 'content/audio/sounds/sheepfield.ogg');
INSERT INTO "sounds" VALUES( 2, 'content/audio/sounds/ships_bell.ogg');
INSERT INTO "sounds" VALUES( 3, 'content/audio/sounds/build.ogg');
INSERT INTO "sounds" VALUES( 4, 'content/audio/sounds/lumberjack.ogg');
INSERT INTO "sounds" VALUES( 5, 'content/audio/sounds/warehouse.ogg');
INSERT INTO "sounds" VALUES( 6, 'content/audio/sounds/main_square.ogg');
INSERT INTO "sounds" VALUES( 7, 'content/audio/sounds/chapel.ogg');
INSERT INTO "sounds" VALUES( 8, 'content/audio/sounds/ships_bell.ogg');
INSERT INTO "sounds" VALUES( 9, 'content/audio/sounds/invalid.ogg');
INSERT INTO "sounds" VALUES(10, 'content/audio/sounds/flippage.ogg');
INSERT INTO "sounds" VALUES(11, 'content/audio/sounds/success.ogg');
INSERT INTO "sounds" VALUES(12, 'content/audio/sounds/refresh.ogg');
INSERT INTO "sounds" VALUES(13, 'content/audio/sounds/click.ogg');

CREATE TABLE "sounds_special" (
	"type" TEXT NOT NULL,
	"sound" INT NOT NULL
);
INSERT INTO "sounds_special" VALUES('build',     3);
INSERT INTO "sounds_special" VALUES('message',   8);
INSERT INTO "sounds_special" VALUES('error',     9);
INSERT INTO "sounds_special" VALUES('flippage', 10);
INSERT INTO "sounds_special" VALUES('success',  11);
INSERT INTO "sounds_special" VALUES('refresh',  12);
INSERT INTO "sounds_special" VALUES('click',    13);

CREATE TABLE "message_icon" (
	"icon_id" INT NOT NULL,
	"up_image" TEXT NOT NULL,
	"down_image" TEXT NOT NULL,
	"hover_image" TEXT NOT NULL
);
INSERT INTO "message_icon" VALUES(1, 'content/gui/icons/widgets/messages/msg_letter_n.png', 'content/gui/icons/widgets/messages/msg_letter_d.png', 'content/gui/icons/widgets/messages/msg_letter_h.png');
INSERT INTO "message_icon" VALUES(2, 'content/gui/icons/widgets/messages/msg_system_n.png', 'content/gui/icons/widgets/messages/msg_system_d.png', 'content/gui/icons/widgets/messages/msg_system_h.png');
INSERT INTO "message_icon" VALUES(3, 'content/gui/icons/widgets/messages/msg_save_n.png',   'content/gui/icons/widgets/messages/msg_save_d.png',   'content/gui/icons/widgets/messages/msg_save_h.png');
INSERT INTO "message_icon" VALUES(4, 'content/gui/icons/widgets/messages/msg_anchor_n.png', 'content/gui/icons/widgets/messages/msg_anchor_d.png', 'content/gui/icons/widgets/messages/msg_anchor_h.png');
INSERT INTO "message_icon" VALUES(5, 'content/gui/icons/widgets/messages/msg_money_n.png',  'content/gui/icons/widgets/messages/msg_money_d.png',  'content/gui/icons/widgets/messages/msg_money_h.png');

CREATE TABLE "collector_restrictions" (
	"collector" INT,
	"object" INT
);
INSERT INTO "collector_restrictions" VALUES(1000011,  4);
INSERT INTO "collector_restrictions" VALUES(1000011,  5);
INSERT INTO "collector_restrictions" VALUES(1000011, 21);
INSERT INTO "collector_restrictions" VALUES(1000011, 32);

CREATE TABLE "message" (
	"text" TEXT NOT NULL,
	"icon" INT NOT NULL,
	"visible_for" REAL NOT NULL,
	"speech_group_id" INT,
	"id_string" TEXT
);
-- When you add new message groups, remember to update  horizons/i18n/voice.py !
INSERT INTO "message" VALUES('{player}: {message}', 1, 30.0, NULL, 'CHAT');
INSERT INTO "message" VALUES('A new settlement was founded by {player}.', 1, 30.0, 2, 'NEW_SETTLEMENT');
INSERT INTO "message" VALUES('A new world has been created.', 1, 15.0, 1, 'NEW_WORLD');
INSERT INTO "message" VALUES('A new ship has been created.', 1, 15.0, 1, 'NEW_UNIT');
INSERT INTO "message" VALUES('Your game has been saved.', 3, 15.0, NULL, 'SAVED_GAME');
INSERT INTO "message" VALUES('Your game has been autosaved.', 3, 15.0, NULL, 'AUTOSAVE');
INSERT INTO "message" VALUES('Your game has been quicksaved.', 3, 15.0, NULL, 'QUICKSAVE');
INSERT INTO "message" VALUES('Screenshot has been saved to {file}.', 2, 20.0, NULL, 'SCREENSHOT');
INSERT INTO "message" VALUES('Your inhabitants reached level {level}.', 1, 30.0, 3, 'SETTLER_LEVEL_UP');
INSERT INTO "message" VALUES('You need more {resource} to build this building.', 1, 10.0, NULL, 'NEED_MORE_RES');
INSERT INTO "message" VALUES('Some of your inhabitants have no access to a main square.', 1, 30.0, NULL, 'NO_MAIN_SQUARE_IN_RANGE');
INSERT INTO "message" VALUES('Some of your inhabitants just moved out.', 1, 40.0, NULL, 'SETTLERS_MOVED_OUT');
INSERT INTO "message" VALUES('You won!', 1, 60.0, NULL, 'YOU_HAVE_WON');
INSERT INTO "message" VALUES('You failed the scenario.', 1, 60.0, NULL, 'YOU_LOST');
INSERT INTO "message" VALUES('Your mine has run out of resources.', 1, 30.0, NULL, 'MINE_EMPTY');
INSERT INTO "message" VALUES('You can also drag roads.', 1, 20.0, NULL, 'DRAG_ROADS_HINT');
INSERT INTO "message" VALUES('{player1} and {player2} have allied their forces.', 1, 10.0, NULL, 'DIPLOMACY_STATUS_NEUTRAL_ALLY');
INSERT INTO "message" VALUES('{player1} and {player2} have ended the war and are now allied.', 1, 10.0, NULL, 'DIPLOMACY_STATUS_ENEMY_ALLY');
INSERT INTO "message" VALUES('{player1} and {player2} have ended their alliance and are now in a state of war.', 1, 10.0, NULL, 'DIPLOMACY_STATUS_ALLY_ENEMY');
INSERT INTO "message" VALUES('{player1} and {player2} will fight each other to the death.', 1, 10.0, NULL, 'DIPLOMACY_STATUS_NEUTRAL_ENEMY');
INSERT INTO "message" VALUES('{player1} and {player2} have terminated their alliance.', 1, 10.0, NULL, 'DIPLOMACY_STATUS_ALLY_NEUTRAL');
INSERT INTO "message" VALUES('{player1} and {player2} have settled their hostility.', 1, 10.0, NULL, 'DIPLOMACY_STATUS_ENEMY_NEUTRAL');
INSERT INTO "message" VALUES('One of your fields requires a farm to harvest its crops.', 1, 30.0, NULL, 'FIELD_NEEDS_FARM');
INSERT INTO "message" VALUES('You have reached the current maximum increment. Your inhabitants will not upgrade further.', 1, 45.0, NULL, 'MAX_INCR_REACHED');
INSERT INTO "message" VALUES('You cannot tear the warehouse, your settlements needs it.', 1, 30.0, NULL, 'WAREHOUSE_NOT_TEARABLE');
INSERT INTO "message" VALUES('The route is now configured. Start it via the "start route" button in the "configure route" menu.', 1, 45.0, NULL, 'ROUTE_DISABLED');
INSERT INTO "message" VALUES('Your crew refuses to leave this map.', 1, 20.0, NULL, 'MOVE_OUTSIDE_OF_WORLD');
INSERT INTO "message" VALUES('Cannot go here.', 1, 20.0, NULL, 'MOVE_INVALID_LOCATION');
INSERT INTO "message" VALUES('Your building has caught fire!', 1, 30.0, NULL, 'BUILDING_ON_FIRE');

CREATE TABLE "ai" (
	"client_id" TEXT NOT NULL,
	"class_package" TEXT NOT NULL,
	"class_name" TEXT NOT NULL
);
INSERT INTO "ai" VALUES('AIPlayer', 'aiplayer', 'AIPlayer');

CREATE TABLE "object_sounds" (
	"object" INT PRIMARY KEY NOT NULL DEFAULT '',
	"sound" INT NOT NULL DEFAULT ''
);
INSERT INTO "object_sounds" VALUES(1, 5);
INSERT INTO "object_sounds" VALUES(4, 6);
INSERT INTO "object_sounds" VALUES(5, 7);
INSERT INTO "object_sounds" VALUES(11, 5);
INSERT INTO "object_sounds" VALUES(18, 1);
INSERT INTO "object_sounds" VALUES(1000010, 4);

CREATE TABLE "related_buildings" (
	"building" INT,
	"related_building" INT,
	"show_in_menu" BOOL NOT NULL DEFAULT ('1')
);
INSERT INTO "related_buildings" VALUES( 3,  4, 1);
INSERT INTO "related_buildings" VALUES( 3,  5, 1);
INSERT INTO "related_buildings" VALUES( 3, 21, 1);
INSERT INTO "related_buildings" VALUES( 3, 32, 1);
INSERT INTO "related_buildings" VALUES( 3, 42, 1);
INSERT INTO "related_buildings" VALUES( 6,  1, 0);
INSERT INTO "related_buildings" VALUES( 8, 17, 1);
INSERT INTO "related_buildings" VALUES(20, 18, 1);
INSERT INTO "related_buildings" VALUES(20, 19, 1);
INSERT INTO "related_buildings" VALUES(20, 22, 1);
INSERT INTO "related_buildings" VALUES(20, 36, 1);
INSERT INTO "related_buildings" VALUES(20, 38, 1);
INSERT INTO "related_buildings" VALUES(20, 39, 1);
INSERT INTO "related_buildings" VALUES(20, 46, 1);
INSERT INTO "related_buildings" VALUES(20, 49, 1);
INSERT INTO "related_buildings" VALUES(20, 60, 1);
INSERT INTO "related_buildings" VALUES(20, 61, 1);
INSERT INTO "related_buildings" VALUES(20, 62, 1);
INSERT INTO "related_buildings" VALUES(45,  3, 0);

CREATE TABLE "mine" (
	"mine" INT NOT NULL,
	"deposit" INT NOT NULL
);
INSERT INTO "mine" VALUES(25, 23);
INSERT INTO "mine" VALUES(28, 34);

CREATE TABLE "tile_set" (
	"ground_id" INT NOT NULL,
	"set_id" TEXT NOT NULL
);
INSERT INTO "tile_set" VALUES(0, 'ts_deep0');
INSERT INTO "tile_set" VALUES(1, 'ts_shallow0');
INSERT INTO "tile_set" VALUES(2, 'ts_shallow-deep0');
INSERT INTO "tile_set" VALUES(3, 'ts_grass0');
INSERT INTO "tile_set" VALUES(4, 'ts_grass-beach0');
INSERT INTO "tile_set" VALUES(5, 'ts_beach-shallow0');
INSERT INTO "tile_set" VALUES(6, 'ts_beach0');

CREATE TABLE "resource" (
	"id" INT NOT NULL,
	"name" TEXT NOT NULL,
	"value" REAL,  -- If NULL, not a physical resource. If 0, just worthless.
	"tradeable" BOOL NOT NULL DEFAULT (0),
	"shown_in_inventory" BOOL NOT NULL DEFAULT (1)
);
INSERT INTO "resource" VALUES( 1, 'coins', 0, 0, 0);
INSERT INTO "resource" VALUES( 2, 'lamb wool', 2, 0, 1);
INSERT INTO "resource" VALUES( 3, 'textile', 6.5, 1, 1);
INSERT INTO "resource" VALUES( 4, 'boards', 1.25, 1, 1);
INSERT INTO "resource" VALUES( 5, 'food', 2, 1, 1);
INSERT INTO "resource" VALUES( 6, 'tools', 18.5, 1, 1);
INSERT INTO "resource" VALUES( 7, 'bricks', 15, 1, 1);
INSERT INTO "resource" VALUES( 8, 'trees', 1, 0, 1);
INSERT INTO "resource" VALUES( 9, 'grass', 0, 0, 0);
-- tradeable   name   value   id   show_inv
INSERT INTO "resource" VALUES(10, 'wool', 2.5, 1, 1);
INSERT INTO "resource" VALUES(11, 'faith', NULL, 0, 1);
INSERT INTO "resource" VALUES(12, 'deer food A', 0, 0, 0);
INSERT INTO "resource" VALUES(13, 'deer meat', 2, 0, 0);
INSERT INTO "resource" VALUES(14, 'happiness', NULL, 0, 0);
INSERT INTO "resource" VALUES(15, 'potatoes', 2, 0, 1);
INSERT INTO "resource" VALUES(16, 'education', NULL, 0, 0);
INSERT INTO "resource" VALUES(17, 'sugar cane', 2, 0, 1);
INSERT INTO "resource" VALUES(18, 'sugar', 2.5, 1, 1);
INSERT INTO "resource" VALUES(19, 'community', NULL, 0, 0);
INSERT INTO "resource" VALUES(20, 'clay deposit', 0, 0, 1);
INSERT INTO "resource" VALUES(21, 'clay', 7.5, 1, 1);
INSERT INTO "resource" VALUES(22, 'liquor', 6.5, 1, 1);
INSERT INTO "resource" VALUES(23, 'charcoal', 6.5, 1, 1);
INSERT INTO "resource" VALUES(24, 'iron deposit', 0, 0, 1);
INSERT INTO "resource" VALUES(25, 'iron ore', 7.5, 1, 1);
INSERT INTO "resource" VALUES(26, 'iron ingots', 24, 1, 1);
INSERT INTO "resource" VALUES(27, 'get-together', NULL, 0, 0);
INSERT INTO "resource" VALUES(28, 'fish', 0, 0, 0);
INSERT INTO "resource" VALUES(29, 'salt', 15, 1, 1);
INSERT INTO "resource" VALUES(30, 'tobacco plants', 2, 0, 1);
INSERT INTO "resource" VALUES(31, 'tobacco leaves', 2.5, 1, 1);
INSERT INTO "resource" VALUES(32, 'tobaccos', 10, 1, 1);
-- tradeable   name   value   id   show_inv
INSERT INTO "resource" VALUES(33, 'cattle', 0, 0, 1);
INSERT INTO "resource" VALUES(34, 'pigs', 0, 0, 1);
INSERT INTO "resource" VALUES(35, 'cattle for slaughter', 2, 0, 1);
INSERT INTO "resource" VALUES(36, 'pigs for slaughter', 2, 0, 1);
INSERT INTO "resource" VALUES(37, 'herbs', 0, 0, 1);
INSERT INTO "resource" VALUES(38, 'medical herbs', 2.5, 0, 0);
INSERT INTO "resource" VALUES(39, 'acorns', 0, 0, 1);
INSERT INTO "resource" VALUES(40, 'cannon', 100, 1, 1);
INSERT INTO "resource" VALUES(41, 'dagger', 10, 0, 0);
INSERT INTO "resource" VALUES(42, 'grain', 0, 0, 1); -- corn ears
INSERT INTO "resource" VALUES(43, 'corn', 2, 0, 1);
INSERT INTO "resource" VALUES(44, 'flour', 2.5, 1, 1);
INSERT INTO "resource" VALUES(45, 'spice plants', 2, 0, 1);
INSERT INTO "resource" VALUES(46, 'spices', 2.5, 1, 1);
INSERT INTO "resource" VALUES(47, 'condiments', 10, 1, 1);
INSERT INTO "resource" VALUES(51, 'stone deposit', 0, 0, 1);
INSERT INTO "resource" VALUES(52, 'stone tops', 7.5, 1, 1);
INSERT INTO "resource" VALUES(53, 'cocoa beans', 2, 0, 1);
INSERT INTO "resource" VALUES(54, 'cocoa', 2.5, 1, 1);
INSERT INTO "resource" VALUES(55, 'confectionery', 10, 1, 1);
INSERT INTO "resource" VALUES(56, 'candles', 10, 1, 1);
INSERT INTO "resource" VALUES(57, 'vines', 2, 0, 1);
INSERT INTO "resource" VALUES(58, 'grapes', 2.5, 1, 1);
-- tradeable   name   value   id   show_inv
INSERT INTO "resource" VALUES(59, 'alvearies', 2, 0, 1);
INSERT INTO "resource" VALUES(60, 'honeycombs', 2.5, 1, 1);
INSERT INTO "resource" VALUES(99, 'fire', NULL, 0, 0);

CREATE TABLE "translucent_buildings" (
	"type" INT
);
INSERT INTO "translucent_buildings" VALUES(17);
INSERT INTO "translucent_buildings" VALUES(34);
INSERT INTO "translucent_buildings" VALUES(28);

CREATE TABLE "weapon" (
	"id" INT,
	"type" TEXT,
	"damage" INT,
	"min_range" INT,
	"max_range" INT,
	"cooldown_time" INT,
	"attack_speed" INT,
	"attack_radius" INT,
	"stackable" BOOL,
	"bullet_image" TEXT
);
INSERT INTO "weapon" VALUES(40, 'ranged', 7, 5, 15, 3, 4, 2, 1, 'content/gfx/misc/cannonballs/cannonball.png');
INSERT INTO "weapon" VALUES(41, 'melee',  3, 1,  1, 3, 2, 1, 0, '');

CREATE TABLE "settler_level" (
	"level" INT NOT NULL,
	"name" TEXT NOT NULL,
	"tax_income" INT NOT NULL,
	"inhabitants_max" INT NOT NULL
);
-------------------------------   tier    name    taxes  max_inhabitants
INSERT INTO "settler_level" VALUES(0, 'Sailors',      3,  2);
INSERT INTO "settler_level" VALUES(1, 'Pioneers',     6,  3);
INSERT INTO "settler_level" VALUES(2, 'Settlers',    10,  5);
INSERT INTO "settler_level" VALUES(3, 'Citizens',    15,  8);
INSERT INTO "settler_level" VALUES(4, 'Merchants',   21, 13);
INSERT INTO "settler_level" VALUES(5, 'Aristocrats', 28, 21);
