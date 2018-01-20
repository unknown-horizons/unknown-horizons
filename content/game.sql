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
--INSERT INTO "sounds" VALUES(14, 'content/audio/sounds/cow.ogg');
INSERT INTO "sounds" VALUES(15, 'content/audio/sounds/smith.ogg');
INSERT INTO "sounds" VALUES(16, 'content/audio/sounds/main_square.ogg');
INSERT INTO "sounds" VALUES(17, 'content/audio/sounds/windmill.ogg');
INSERT INTO "sounds" VALUES(18, 'content/audio/sounds/tavern.ogg');
INSERT INTO "sounds" VALUES(19, 'content/audio/sounds/stonemason.ogg');

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

CREATE TABLE "message" (
	"id_string" TEXT NOT NULL,
	"icon" INT NOT NULL,
	"visible_for" REAL NOT NULL,
	"speech_group_id" INT
); -- When you add new message groups, remember to update  horizons/i18n/voice.py !
INSERT INTO "message" VALUES('AUTOSAVE',         3, 15.0, NULL);
INSERT INTO "message" VALUES('BUILDING_ON_FIRE', 6, 30.0, NULL);
INSERT INTO "message" VALUES('CHAT',             1, 30.0, NULL);
INSERT INTO "message" VALUES('DIPLOMACY_STATUS_ALLY_ENEMY',    1, 10.0, NULL);
INSERT INTO "message" VALUES('DIPLOMACY_STATUS_ALLY_NEUTRAL',  1, 10.0, NULL);
INSERT INTO "message" VALUES('DIPLOMACY_STATUS_ENEMY_ALLY',    1, 10.0, NULL);
INSERT INTO "message" VALUES('DIPLOMACY_STATUS_ENEMY_NEUTRAL', 1, 10.0, NULL);
INSERT INTO "message" VALUES('DIPLOMACY_STATUS_NEUTRAL_ALLY',  1, 10.0, NULL);
INSERT INTO "message" VALUES('DIPLOMACY_STATUS_NEUTRAL_ENEMY', 1, 10.0, NULL);
INSERT INTO "message" VALUES('DRAG_ROADS_HINT',  1, 20.0, NULL);
INSERT INTO "message" VALUES('FIELD_NEEDS_FARM', 1, 30.0, NULL);
INSERT INTO "message" VALUES('MAX_TIER_REACHED', 1, 45.0, NULL);
INSERT INTO "message" VALUES('MINE_EMPTY',       1, 30.0, NULL);
INSERT INTO "message" VALUES('MOVE_INVALID_LOCATION', 1, 20.0, NULL);
INSERT INTO "message" VALUES('MOVE_OUTSIDE_OF_WORLD', 1, 20.0, NULL);
INSERT INTO "message" VALUES('NEED_MORE_RES',    1, 10.0, NULL);
INSERT INTO "message" VALUES('NEW_SETTLEMENT',   4, 30.0, 2);
INSERT INTO "message" VALUES('NEW_WORLD',        1, 15.0, 1);
INSERT INTO "message" VALUES('NEW_SHIP',         1, 15.0, NULL);
INSERT INTO "message" VALUES('NEW_SOLDIER',      1, 15.0, NULL);
INSERT INTO "message" VALUES('NEW_INHABITANT',   1, 15.0, NULL);
INSERT INTO "message" VALUES('NO_MAIN_SQUARE_IN_RANGE', 1, 30.0, NULL);
INSERT INTO "message" VALUES('QUICKSAVE',        3, 15.0, NULL);
INSERT INTO "message" VALUES('ROUTE_DISABLED',   2, 45.0, NULL);
INSERT INTO "message" VALUES('SAVED_GAME',       3, 15.0, NULL);
INSERT INTO "message" VALUES('SCREENSHOT',       2, 20.0, NULL);
INSERT INTO "message" VALUES('SETTLER_LEVEL_UP', 1, 30.0, 3);
INSERT INTO "message" VALUES('SETTLERS_MOVED_OUT', 1, 40.0, NULL);
INSERT INTO "message" VALUES('WAREHOUSE_NOT_TEARABLE', 1, 30.0, NULL);
INSERT INTO "message" VALUES('YOU_HAVE_WON',     1, 60.0, NULL);
INSERT INTO "message" VALUES('YOU_LOST',         1, 60.0, NULL);
INSERT INTO "message" VALUES('BUILDING_INFECTED_BY_BLACK_DEATH', 7, 30.0, NULL);

CREATE TABLE "message_text" (
	"id_string" TEXT NOT NULL,
	"text" TEXT NOT NULL
);
INSERT INTO "message_text" VALUES('AUTOSAVE',         'Your game has been autosaved.');
INSERT INTO "message_text" VALUES('BUILDING_ON_FIRE', 'Your building has caught fire!');
INSERT INTO "message_text" VALUES('CHAT',             '{player}: {message}');
INSERT INTO "message_text" VALUES('DIPLOMACY_STATUS_ALLY_ENEMY',    '{player1} and {player2} have ended their alliance and are now in a state of war.');
INSERT INTO "message_text" VALUES('DIPLOMACY_STATUS_ALLY_NEUTRAL',  '{player1} and {player2} have terminated their alliance.');
INSERT INTO "message_text" VALUES('DIPLOMACY_STATUS_ENEMY_ALLY',    '{player1} and {player2} have ended the war and are now allied.');
INSERT INTO "message_text" VALUES('DIPLOMACY_STATUS_ENEMY_NEUTRAL', '{player1} and {player2} have settled their hostility.');
INSERT INTO "message_text" VALUES('DIPLOMACY_STATUS_NEUTRAL_ALLY',  '{player1} and {player2} have allied their forces.');
INSERT INTO "message_text" VALUES('DIPLOMACY_STATUS_NEUTRAL_ENEMY', '{player1} and {player2} will fight each other to the death.');
INSERT INTO "message_text" VALUES('DRAG_ROADS_HINT',  'You can also drag roads.');
INSERT INTO "message_text" VALUES('FIELD_NEEDS_FARM', 'One of your fields requires a farm to harvest its crops.');
INSERT INTO "message_text" VALUES('MINE_EMPTY',       'Your mine has run out of resources.');
INSERT INTO "message_text" VALUES('MAX_TIER_REACHED', 'You have reached the current maximum tier. Your inhabitants will not upgrade further.');
INSERT INTO "message_text" VALUES('MOVE_INVALID_LOCATION', 'Cannot go here.');
INSERT INTO "message_text" VALUES('MOVE_OUTSIDE_OF_WORLD', 'Your crew refuses to leave this map.');
INSERT INTO "message_text" VALUES('NEED_MORE_RES',    'You need more {resource} to build this building.');
INSERT INTO "message_text" VALUES('NEW_SETTLEMENT',   'A new settlement was founded by {player}.');
INSERT INTO "message_text" VALUES('NEW_SHIP',         'A new ship by the name of {name} has been created.');
INSERT INTO "message_text" VALUES('NEW_SOLDIER',      'The Soldier by the name of {name} is ready to battle.');
INSERT INTO "message_text" VALUES('NEW_INHABITANT',   'The inhabitant by the name of {name} is available.');
INSERT INTO "message_text" VALUES('NEW_WORLD',        'A new world has been created.');
INSERT INTO "message_text" VALUES('NO_MAIN_SQUARE_IN_RANGE', 'Some of your inhabitants have no access to a main square.');
INSERT INTO "message_text" VALUES('QUICKSAVE',        'Your game has been quicksaved.');
INSERT INTO "message_text" VALUES('ROUTE_DISABLED',   'The route is now configured. Start it via the "start route" button in the "configure route" menu.');
INSERT INTO "message_text" VALUES('SAVED_GAME',       'Your game has been saved.');
INSERT INTO "message_text" VALUES('SCREENSHOT',       'Screenshot has been saved to {file}.');
INSERT INTO "message_text" VALUES('SETTLER_LEVEL_UP', 'Your inhabitants reached level {level}.');
INSERT INTO "message_text" VALUES('SETTLERS_MOVED_OUT', 'Some of your inhabitants just moved out.');
INSERT INTO "message_text" VALUES('WAREHOUSE_NOT_TEARABLE', 'You cannot tear the warehouse, your settlements needs it.');
INSERT INTO "message_text" VALUES('YOU_HAVE_WON',     'You won!');
INSERT INTO "message_text" VALUES('YOU_LOST',         'You failed the scenario.');
INSERT INTO "message_text" VALUES('BUILDING_INFECTED_BY_BLACK_DEATH', 'The inhabitants of this building are infected by the Black Death!');

CREATE TABLE "message_icon" (
	"icon_id" INT NOT NULL,
	"path" TEXT NOT NULL
);
INSERT INTO "message_icon" VALUES(1, 'icons/widgets/messages/msg_letter');
INSERT INTO "message_icon" VALUES(2, 'icons/widgets/messages/msg_system');
INSERT INTO "message_icon" VALUES(3, 'icons/widgets/messages/msg_save');
INSERT INTO "message_icon" VALUES(4, 'icons/widgets/messages/msg_anchor');
INSERT INTO "message_icon" VALUES(5, 'icons/widgets/messages/msg_money');
INSERT INTO "message_icon" VALUES(6, 'icons/widgets/messages/msg_disaster_fire');
INSERT INTO "message_icon" VALUES(7, 'icons/widgets/messages/msg_disaster_plague');

CREATE TABLE "ai" (
	"client_id" TEXT NOT NULL,
	"class_package" TEXT NOT NULL,
	"class_name" TEXT NOT NULL
);
INSERT INTO "ai" VALUES('AIPlayer', 'aiplayer', 'AIPlayer');

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
INSERT INTO "related_buildings" VALUES(20, 40, 1);
INSERT INTO "related_buildings" VALUES(20, 46, 1);
INSERT INTO "related_buildings" VALUES(20, 49, 1);
INSERT INTO "related_buildings" VALUES(20, 60, 1);
INSERT INTO "related_buildings" VALUES(20, 61, 1);
INSERT INTO "related_buildings" VALUES(20, 62, 1);
INSERT INTO "related_buildings" VALUES(20, 69, 1);
INSERT INTO "related_buildings" VALUES(45,  3, 0);

CREATE TABLE "tile_set" (
	"ground_id" INT NOT NULL,
	"set_id" TEXT NOT NULL
);
INSERT INTO "tile_set" VALUES(0, 'ts_deep0');
INSERT INTO "tile_set" VALUES(1, 'ts_shallow0');
INSERT INTO "tile_set" VALUES(2, 'ts_shallow-deep0');
INSERT INTO "tile_set" VALUES(3, 'ts_grass0');
INSERT INTO "tile_set" VALUES(3, 'ts_grass1');
INSERT INTO "tile_set" VALUES(3, 'ts_grass2');
INSERT INTO "tile_set" VALUES(3, 'ts_grass3');
INSERT INTO "tile_set" VALUES(3, 'ts_grass4');
INSERT INTO "tile_set" VALUES(3, 'ts_grass5');
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
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES( 1, 'coins',           0,     0,    0);
INSERT INTO "resource" VALUES( 2, 'lamb wool',       2,     0,    1);
INSERT INTO "resource" VALUES( 3, 'textile',         6.5,   1,    1);
INSERT INTO "resource" VALUES( 4, 'boards',          2,     1,    1);
INSERT INTO "resource" VALUES( 5, 'food',            2,     1,    1);
INSERT INTO "resource" VALUES( 6, 'tools',          21,     1,    1);
INSERT INTO "resource" VALUES( 7, 'bricks',         15,     1,    1);
INSERT INTO "resource" VALUES( 8, 'trees',           1,     0,    1);
INSERT INTO "resource" VALUES( 9, 'grass',           0,     0,    0);
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(10, 'wool',            2.5,   1,    1);
INSERT INTO "resource" VALUES(11, 'faith',          NULL,   0,    0);
INSERT INTO "resource" VALUES(12, 'deer food A',     0,     0,    0);
INSERT INTO "resource" VALUES(13, 'deer meat',       2,     0,    0);
INSERT INTO "resource" VALUES(14, 'happiness',      NULL,   0,    0);
INSERT INTO "resource" VALUES(15, 'potatoes',        2,     0,    1);
INSERT INTO "resource" VALUES(16, 'education',      NULL,   0,    0);
INSERT INTO "resource" VALUES(17, 'sugar cane',      2,     0,    1);
INSERT INTO "resource" VALUES(18, 'sugar',           2.5,   1,    1);
INSERT INTO "resource" VALUES(19, 'community',      NULL,   0,    0);
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(20, 'clay deposit',    0,     0,    1);
INSERT INTO "resource" VALUES(21, 'clay',            7.5,   1,    1);
INSERT INTO "resource" VALUES(22, 'liquor',          6.5,   1,    1);
INSERT INTO "resource" VALUES(23, 'charcoal',        8,     1,    1);
INSERT INTO "resource" VALUES(24, 'iron deposit',    0,     0,    1);
INSERT INTO "resource" VALUES(25, 'iron ore',        7.5,   1,    1);
INSERT INTO "resource" VALUES(26, 'iron ingots',    25,     1,    1);
INSERT INTO "resource" VALUES(27, 'get-together',   NULL,   0,    0);
INSERT INTO "resource" VALUES(28, 'fish',            0,     0,    0);
INSERT INTO "resource" VALUES(29, 'salt',           15,     1,    1);
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(30, 'tobacco plants',  2,     0,    1);
INSERT INTO "resource" VALUES(31, 'tobacco leaves',  2.5,   1,    1);
INSERT INTO "resource" VALUES(32, 'tobaccos',       10,     1,    1);
INSERT INTO "resource" VALUES(33, 'cattle',          0,     0,    1);
INSERT INTO "resource" VALUES(34, 'pigs',            0,     0,    0);
INSERT INTO "resource" VALUES(35, 'cattle for slaughter',2, 0,    1);
INSERT INTO "resource" VALUES(36, 'pigs for slaughter',2,   0,    0);
INSERT INTO "resource" VALUES(37, 'herbs',           0,     0,    1);
INSERT INTO "resource" VALUES(38, 'medical herbs',   2.5,   1,    1);
INSERT INTO "resource" VALUES(39, 'acorns',          0,     0,    0); -- unused
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(40, 'cannon',        100,     1,    1);
INSERT INTO "resource" VALUES(41, 'sword',          10,     1,    1);
INSERT INTO "resource" VALUES(42, 'grain',           0,     0,    1); -- (corn ears)
INSERT INTO "resource" VALUES(43, 'corn',            2,     0,    1);
INSERT INTO "resource" VALUES(44, 'flour',           2.5,   1,    1);
INSERT INTO "resource" VALUES(45, 'spice plants',    2,     0,    1);
INSERT INTO "resource" VALUES(46, 'spices',          2.5,   0,    1);
INSERT INTO "resource" VALUES(47, 'condiments',     10,     0,    1);
INSERT INTO "resource" VALUES(48, 'marble deposit',  0,     0,    0); -- unused
INSERT INTO "resource" VALUES(49, 'marble tops',     7.5,   0,    0); -- unused
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(50, 'coal deposit',    0,     0,    0); -- unused
INSERT INTO "resource" VALUES(51, 'stone deposit',   0,     0,    1);
INSERT INTO "resource" VALUES(52, 'stone tops',      7.5,   0,    1);
INSERT INTO "resource" VALUES(53, 'cocoa beans',     2,     0,    1);
INSERT INTO "resource" VALUES(54, 'cocoa',           2.5,   0,    0);
INSERT INTO "resource" VALUES(55, 'confectionery',  10,     0,    1);
INSERT INTO "resource" VALUES(56, 'candles',        10,     0,    1);
INSERT INTO "resource" VALUES(57, 'vines',           2,     0,    1); 
INSERT INTO "resource" VALUES(58, 'grapes',          2.5,   0,    1);
INSERT INTO "resource" VALUES(59, 'alvearies',       2,     0,    1);
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(60, 'honeycombs',      2.5,   0,    1);
INSERT INTO "resource" VALUES(61, 'gold deposit',    0,     0,    0); -- unused
INSERT INTO "resource" VALUES(62, 'gold ore',       15,     0,    0); -- unused
INSERT INTO "resource" VALUES(63, 'gold ingots',    50,     0,    0); -- unused
INSERT INTO "resource" VALUES(64, 'gem deposit',     0,     0,    0); -- unused
INSERT INTO "resource" VALUES(65, 'rough gems',     15,     0,    0); -- unused
INSERT INTO "resource" VALUES(66, 'gems',           50,     0,    0); -- unused
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(70, 'coffee plants',   2,     0,    0); -- unused
INSERT INTO "resource" VALUES(71, 'coffee beans',    2.5,   0,    0); -- unused
INSERT INTO "resource" VALUES(72, 'coffee',         10,     0,    0); -- unused
INSERT INTO "resource" VALUES(73, 'tea plants',      2,     0,    0); -- unused
INSERT INTO "resource" VALUES(74, 'tea leaves',      2.5,   0,    0); -- unused
INSERT INTO "resource" VALUES(75, 'tea',            10,     0,    0); -- unused
INSERT INTO "resource" VALUES(76, 'flower meadows',  2,     0,    0); -- unused
INSERT INTO "resource" VALUES(77, 'blossoms',        5,     0,    0); -- unused
INSERT INTO "resource" VALUES(78, 'brine deposit',   0,     0,    0); -- unused
INSERT INTO "resource" VALUES(79, 'brine',           5,     0,    0); -- unused
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(80, 'whales',         10,     0,    0); -- unused -- (blubber meat cetaceum baleen)
INSERT INTO "resource" VALUES(81, 'ambergris',      10,     0,    0); -- unused -- (solid, waxy, flammable, dull grey)
INSERT INTO "resource" VALUES(82, 'lamp oil',       10,     0,    0); -- unused -- (via blubber)
INSERT INTO "resource" VALUES(83, 'cotton plants',   2,     0,    0); -- unused -- (called gossypium)
INSERT INTO "resource" VALUES(84, 'cotton',          2.5,   0,    0); -- unused -- (fibers)
INSERT INTO "resource" VALUES(85, 'indigo plants' ,  2,     0,    0); -- unused -- (called indigofera)
INSERT INTO "resource" VALUES(86, 'indigo',          5,     0,    0); -- unused
INSERT INTO "resource" VALUES(87, 'garments',       20,     0,    0); -- unused
INSERT INTO "resource" VALUES(88, 'perfume',        20,     0,    0); -- unused
INSERT INTO "resource" VALUES(89, 'hop plants',      2,     0,    0);
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(90, 'hops',            2.5,   0,    1);
INSERT INTO "resource" VALUES(91, 'beer',            6.5,   1,    1);
-- vegetables, fruit, hemp, ropes
-- almonds, almond milk
-- hides, leather, shoes, saddles
-- tin ore, copper ore, tin, copper, bronze
-- mortars, [swords maces muskets spears arbalests]
--                            id   name            value  trade  show_inv
INSERT INTO "resource" VALUES(96, 'hygiene',        NULL,   0,    0); -- (public bath)
INSERT INTO "resource" VALUES(97, 'recreation',     NULL,   0,    0); -- (for aesthetics)
INSERT INTO "resource" VALUES(98, 'blackdeath',     NULL,   0,    0); -- (doctor)
INSERT INTO "resource" VALUES(99, 'fire',           NULL,   0,    0); -- (fire service)
-- "unused": not used by game code currently, thus made untradable and hidden from inventories

CREATE TABLE "weapon" (
	"id" INT,
	"type" TEXT,
	"damage" INT,
	"min_range" INT,
	"max_range" INT,
	"cooldown_time" INT,
	"attack_speed" INT,
	"attack_radius" INT,
	"stackable" BOOL
);
INSERT INTO "weapon" VALUES(40, 'ranged', 7, 5, 15, 3, 4, 2, 1);
INSERT INTO "weapon" VALUES(41, 'melee',  3, 1,  1, 3, 2, 1, 0);

CREATE TABLE "tier" (
	"level" INT NOT NULL,
	"name" TEXT NOT NULL,
	"tax_income" INT NOT NULL,
	"inhabitants_max" INT NOT NULL
);
----------------------   tier    name    taxes  max_inhabitants
INSERT INTO "tier" VALUES(0, 'Sailors',      3,  2);
INSERT INTO "tier" VALUES(1, 'Pioneers',     6,  3);
INSERT INTO "tier" VALUES(2, 'Settlers',    10,  5);
INSERT INTO "tier" VALUES(3, 'Citizens',    15,  8);
INSERT INTO "tier" VALUES(4, 'Merchants',   21, 13);
INSERT INTO "tier" VALUES(5, 'Aristocrats', 28, 21);
