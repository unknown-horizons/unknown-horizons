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
	"name" TEXT NOT NULL,
	"class_package" TEXT NOT NULL,
	"class_type" TEXT NOT NULL,
	"base_velocity" REAL DEFAULT '12.0',
	"radius" INT DEFAULT 5,
	"id" INT
);
INSERT INTO "unit" VALUES('Huker', 'ship', 'Ship', 5.0, 5, 1000001);
INSERT INTO "unit" VALUES('BuildingCollector', 'collectors', 'BuildingCollector', 12.0, 5, 1000002);
INSERT INTO "unit" VALUES('Sheep', 'animal', 'FarmAnimal', 12.0, 3, 1000003);
INSERT INTO "unit" VALUES('Fisher', 'ship', 'FisherShip', 12.0, 5, 1000004);
INSERT INTO "unit" VALUES('Pirate Ship', 'ship', 'PirateShip', 12.0, 5, 1000005);
INSERT INTO "unit" VALUES('Trader', 'ship', 'TradeShip', 12.0, 8, 1000006);
INSERT INTO "unit" VALUES('AnimalCarriage', 'collectors', 'AnimalCollector', 12.0, 5, 1000007);
INSERT INTO "unit" VALUES('StorageCollector', 'collectors', 'StorageCollector', 12.0, 5, 1000008);
INSERT INTO "unit" VALUES('FieldCollector', 'collectors', 'FieldCollector', 12.0, 5, 1000009);
INSERT INTO "unit" VALUES('LumberjackCollector', 'collectors', 'FieldCollector', 12.0, 5, 1000010);
INSERT INTO "unit" VALUES('SettlerCollector', 'collectors', 'StorageCollector', 12.0, 5, 1000011);
INSERT INTO "unit" VALUES('Deer', 'animal', 'WildAnimal', 12.0, 5, 1000013);
INSERT INTO "unit" VALUES('HunterCollector', 'collectors', 'HunterCollector', 12.0, 5, 1000014);
INSERT INTO "unit" VALUES('FarmAnimalCollector', 'collectors', 'FarmAnimalCollector', 12.0, 5, 1000015);
INSERT INTO "unit" VALUES('UsableFisher', 'ship', 'Ship', 12.0, 5, 1000016);
INSERT INTO "unit" VALUES('Cattle', 'animal', 'FarmAnimal', 12.0, 3, 1000017);
INSERT INTO "unit" VALUES('Boar', 'animal', 'FarmAnimal', 12.0, 5, 1000018);
INSERT INTO "unit" VALUES('Doctor', 'collectors', 'DisasterRecoveryCollector', 12.0, 5, 1000019);
INSERT INTO "unit" VALUES('Frigate', 'fightingship', 'FightingShip', 12.0, 5, 1000020);
INSERT INTO "unit" VALUES('BomberMan', 'groundunit', 'FightingGroundUnit', 10.0, 5, 1000021);
INSERT INTO "unit" VALUES('Firefighter', 'collectors', 'DisasterRecoveryCollector', 12.0, 5, 1000022);

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
	"file" TEXT NOT NULL DEFAULT '',
	"id" NOT NULL DEFAULT -1
);
INSERT INTO "sounds" VALUES('content/audio/sounds/sheepfield.ogg',  1);
INSERT INTO "sounds" VALUES('content/audio/sounds/ships_bell.ogg',  2);
INSERT INTO "sounds" VALUES('content/audio/sounds/build.ogg',       3);
INSERT INTO "sounds" VALUES('content/audio/sounds/lumberjack.ogg',  4);
INSERT INTO "sounds" VALUES('content/audio/sounds/warehouse.ogg',   5);
INSERT INTO "sounds" VALUES('content/audio/sounds/main_square.ogg', 6);
INSERT INTO "sounds" VALUES('content/audio/sounds/chapel.ogg',      7);
INSERT INTO "sounds" VALUES('content/audio/sounds/ships_bell.ogg',  8);
INSERT INTO "sounds" VALUES('content/audio/sounds/invalid.ogg',     9);
INSERT INTO "sounds" VALUES('content/audio/sounds/flippage.ogg',   10);
INSERT INTO "sounds" VALUES('content/audio/sounds/success.ogg',    11);
INSERT INTO "sounds" VALUES('content/audio/sounds/refresh.ogg',    12);
INSERT INTO "sounds" VALUES('content/audio/sounds/click.ogg',      13);

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
	"sound" INT NOT NULL DEFAULT '');
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
INSERT INTO "related_buildings" VALUES(8, 17, 1);
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
INSERT INTO "related_buildings" VALUES(3, 4, 1);
INSERT INTO "related_buildings" VALUES(3, 5, 1);
INSERT INTO "related_buildings" VALUES(3, 21, 1);
INSERT INTO "related_buildings" VALUES(3, 32, 1);
INSERT INTO "related_buildings" VALUES(3, 42, 1);
INSERT INTO "related_buildings" VALUES(6, 1, 0);
INSERT INTO "related_buildings" VALUES(45, 3, 0);

CREATE TABLE "mine" (
	"mine" INT NOT NULL,
	"deposit" INT NOT NULL
);
INSERT INTO "mine" VALUES(25, 23);
INSERT INTO "mine" VALUES(28, 34);

CREATE TABLE "tile_set" (
	"set_id" TEXT NOT NULL,
	"ground_id" INT NOT NULL
);
INSERT INTO "tile_set" VALUES('ts_deep0', 0);
INSERT INTO "tile_set" VALUES('ts_shallow0', 1);
INSERT INTO "tile_set" VALUES('ts_shallow-deep0', 2);
INSERT INTO "tile_set" VALUES('ts_grass0', 3);
INSERT INTO "tile_set" VALUES('ts_grass-beach0', 4);
INSERT INTO "tile_set" VALUES('ts_beach-shallow0', 5);
INSERT INTO "tile_set" VALUES('ts_beach0', 6);

CREATE TABLE "resource" (
	"tradeable" BOOL NOT NULL DEFAULT (0),
	"name" TEXT NOT NULL,
	"value" REAL,
	"id" INT NOT NULL,
	"shown_in_inventory" BOOL NOT NULL DEFAULT (1)
);
INSERT INTO "resource" VALUES(0, 'coins', 0, 1, 0);
INSERT INTO "resource" VALUES(0, 'lamb wool', 2, 2, 1);
INSERT INTO "resource" VALUES(1, 'textile', 6.5, 3, 1);
INSERT INTO "resource" VALUES(1, 'boards', 1.25, 4, 1);
INSERT INTO "resource" VALUES(1, 'food', 2, 5, 1);
INSERT INTO "resource" VALUES(1, 'tools', 18.5, 6, 1);
INSERT INTO "resource" VALUES(1, 'bricks', 15, 7, 1);
INSERT INTO "resource" VALUES(0, 'trees', 1, 8, 1);
INSERT INTO "resource" VALUES(0, 'grass', 0, 9, 0);
-- tradeable   name   value   id   show_inv
INSERT INTO "resource" VALUES(1, 'wool', 2.5, 10, 1);
INSERT INTO "resource" VALUES(0, 'faith', NULL, 11, 1);
INSERT INTO "resource" VALUES(0, 'deer food A', 0, 12, 0);
INSERT INTO "resource" VALUES(0, 'deer meat', 2, 13, 0);
INSERT INTO "resource" VALUES(0, 'happiness', NULL, 14, 0);
INSERT INTO "resource" VALUES(0, 'potatoes', 2, 15, 1);
INSERT INTO "resource" VALUES(0, 'education', NULL, 16, 0);
INSERT INTO "resource" VALUES(0, 'sugar cane', 2, 17, 1);
INSERT INTO "resource" VALUES(1, 'sugar', 2.5, 18, 1);
INSERT INTO "resource" VALUES(0, 'community', NULL, 19, 0);
INSERT INTO "resource" VALUES(0, 'clay deposit', 0, 20, 1);
INSERT INTO "resource" VALUES(1, 'clay', 7.5, 21, 1);
INSERT INTO "resource" VALUES(1, 'liquor', 6.5, 22, 1);
INSERT INTO "resource" VALUES(1, 'charcoal', 6.5, 23, 1);
INSERT INTO "resource" VALUES(0, 'iron deposit', 0, 24, 1);
INSERT INTO "resource" VALUES(1, 'iron ore', 7.5, 25, 1);
INSERT INTO "resource" VALUES(1, 'iron ingots', 24, 26, 1);
INSERT INTO "resource" VALUES(0, 'get-together', NULL, 27, 0);
INSERT INTO "resource" VALUES(0, 'fish', 0, 28, 0);
INSERT INTO "resource" VALUES(1, 'salt', 15, 29, 1);
INSERT INTO "resource" VALUES(0, 'tobacco plants', 2, 30, 1);
INSERT INTO "resource" VALUES(1, 'tobacco leaves', 2.5, 31, 1);
INSERT INTO "resource" VALUES(1, 'tobaccos', 10, 32, 1);
-- tradeable   name   value   id   show_inv
INSERT INTO "resource" VALUES(0, 'cattle', 0, 33, 1);
INSERT INTO "resource" VALUES(0, 'pigs', 0, 34, 1);
INSERT INTO "resource" VALUES(0, 'cattle for slaughter', 2, 35, 1);
INSERT INTO "resource" VALUES(0, 'pigs for slaughter', 2, 36, 1);
INSERT INTO "resource" VALUES(0, 'herbs', 0, 37, 1);
INSERT INTO "resource" VALUES(0, 'medical herbs', 2.5, 38, 0);
INSERT INTO "resource" VALUES(0, 'acorns', 0, 39, 1);
INSERT INTO "resource" VALUES(1, 'cannon', 100, 40, 1);
INSERT INTO "resource" VALUES(0, 'dagger', 10, 41, 0);
INSERT INTO "resource" VALUES(0, 'grain', 0, 42, 1); -- corn ears
INSERT INTO "resource" VALUES(0, 'corn', 2, 43, 1);
INSERT INTO "resource" VALUES(1, 'flour', 2.5, 44, 1);
INSERT INTO "resource" VALUES(0, 'spice plants', 2, 45, 1);
INSERT INTO "resource" VALUES(1, 'spices', 2.5, 46, 1);
INSERT INTO "resource" VALUES(1, 'condiments', 10, 47, 1);
INSERT INTO "resource" VALUES(0, 'stone deposit', 0, 51, 1);
INSERT INTO "resource" VALUES(1, 'stone tops', 7.5, 52, 1);
INSERT INTO "resource" VALUES(0, 'cocoa beans', 2, 53, 1);
INSERT INTO "resource" VALUES(1, 'cocoa', 2.5, 54, 1);
INSERT INTO "resource" VALUES(1, 'confectionery', 10, 55, 1);
INSERT INTO "resource" VALUES(1, 'candles', 10, 56, 1);
INSERT INTO "resource" VALUES(0, 'vines', 2, 57, 1);
INSERT INTO "resource" VALUES(1, 'grapes', 2.5, 58, 1);
-- tradeable   name   value   id   show_inv
INSERT INTO "resource" VALUES(0, 'alvearies', 2, 59, 1);
INSERT INTO "resource" VALUES(1, 'honeycombs', 2.5, 60, 1);
INSERT INTO "resource" VALUES(0, 'fire', 0, 99, 0);

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
INSERT INTO "weapon" VALUES(41, 'melee', 3, 1, 1, 3, 2, 1, 0, '');

CREATE TABLE "settler_level" (
	"level" INT NOT NULL DEFAULT (''),
	"name" TEXT NOT NULL DEFAULT (''),
	"tax_income" INT NOT NULL DEFAULT (''),
	"inhabitants_max" INT
);
-------------------------------   tier    name    taxes  max_inhabitants
INSERT INTO "settler_level" VALUES(0, 'Sailors',      3,  2);
INSERT INTO "settler_level" VALUES(1, 'Pioneers',     6,  3);
INSERT INTO "settler_level" VALUES(2, 'Settlers',    10,  5);
INSERT INTO "settler_level" VALUES(3, 'Citizens',    15,  8);
INSERT INTO "settler_level" VALUES(4, 'Merchants',   21, 13);
INSERT INTO "settler_level" VALUES(5, 'Aristocrats', 28, 21);
