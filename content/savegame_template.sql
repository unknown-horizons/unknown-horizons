PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE `map_properties` (`name` TEXT NOT NULL, `value` TEXT NOT NULL);
CREATE TABLE `name` (`name` TEXT NOT NULL);
CREATE TABLE `island` (`x` INTEGER NOT NULL, `y` INTEGER NOT NULL, `file` TEXT NOT NULL);
CREATE TABLE `storage` (`object` INTEGER NOT NULL, `resource` INTEGER NOT NULL, `amount` INTEGER NOT NULL);
CREATE TABLE `collector_job` (`object` INTEGER DEFAULT NULL, `resource` INTEGER DEFAULT NULL, `amount` INTEGER DEFAULT NULL);
CREATE TABLE "unit_path" (`unit` INTEGER NOT NULL, `index` INTEGER NOT NULL, `location` INTEGER DEFAULT NULL, `x` INTEGER DEFAULT NULL, `y` INTEGER DEFAULT NULL);
CREATE TABLE `metadata` (`name` TEXT NOT NULL  DEFAULT '', `value` TEXT DEFAULT '');
CREATE TABLE `view` (`zoom` FLOAT NOT NULL  DEFAULT '', `rotation` FLOAT NOT NULL  DEFAULT '', `location_x` INTEGER NOT NULL  DEFAULT '', `location_y` INTEGER NOT NULL  DEFAULT '');
CREATE TABLE "selected" (`group` INTEGER DEFAULT '', `id` INTEGER NOT NULL  DEFAULT '');
CREATE TABLE `command` (`tick` INTEGER NOT NULL , `issuer` INTEGER NOT NULL , `data` TEXT NOT NULL );
ANALYZE sqlite_master;
CREATE TABLE "building" ("type" INTEGER,"x" INTEGER,"y" INTEGER,"location" INTEGER, "rotation" INTEGER, "level" INTEGER NOT NULL  DEFAULT 0);
CREATE TABLE "storage_properties" ("object" INTEGER NOT NULL ,"name" TEXT NOT NULL , "value" TEXT);
CREATE TABLE "trade_buy" (object INTEGER NOT NULL, "resource" INTEGER NOT NULL , "trade_limit" INTEGER NOT NULL);
CREATE TABLE "trade_sell" (object INTEGER NOT NULL, "resource" INTEGER NOT NULL , "trade_limit" INTEGER NOT NULL);
CREATE TABLE "collector" ("state" INTEGER NOT NULL ,"remaining_ticks" INTEGER, "start_hidden" BOOLEAN NOT NULL  DEFAULT '1');
CREATE TABLE "trader_ships" ("state" INTEGER NOT NULL , remaining_ticks INTEGER, "targeted_warehouse" INTEGER);
CREATE TABLE wildanimal (can_reproduce BOOL, health INTEGER);
CREATE TABLE "message_widget_active" ("id" INTEGER NOT NULL  DEFAULT '' ,"read" INTEGER NOT NULL  DEFAULT '' ,"created" INTEGER NOT NULL  DEFAULT '' ,"display" INTEGER NOT NULL  DEFAULT '' ,"message" TEXT NOT NULL  DEFAULT '' , "x" INTEGER, "y" INTEGER);
CREATE TABLE "message_widget_archive" ("id" INTEGER NOT NULL  DEFAULT '' ,"read" INTEGER NOT NULL  DEFAULT '' ,"created" INTEGER NOT NULL  DEFAULT '' ,"display" INTEGER NOT NULL  DEFAULT '' ,"message" TEXT NOT NULL  DEFAULT '' , "x" INTEGER, "y" INTEGER);
CREATE TABLE concrete_object(id int, action_runtime int);
CREATE TABLE metadata_blob (name TEXT NOT NULL, value BLOB);
CREATE TABLE "pirate_ships" ("state" INTEGER NOT NULL  DEFAULT 0, "remaining_ticks" INTEGER DEFAULT 0);
CREATE TABLE storage_global_limit(object INT NOT NULL, value INT NOT NULL);
CREATE TABLE storage_slot_limit(object INT NOT NULL, slot INT NOT NULL, value INT NOT NULL);
CREATE TABLE "scenario_variables" ("key" TEXT NOT NULL , "value" TEXT NOT NULL );
CREATE TABLE logbook ( widgets string );
CREATE TABLE "trade_values" ("object" INTEGER NOT NULL , "total_income" INTEGER NOT NULL , "total_expenses" INTEGER NOT NULL );
CREATE TABLE mine(deposit_class INTEGER NOT NULL, mine_empty_msg_shown BOOL);
CREATE TABLE settlement_produced_res(settlement INT NOT NULL, res INT NOT NULL, amount INT NOT NULL);
CREATE TABLE remaining_ticks_of_month(ticks INTEGER);
CREATE TABLE "pirate_home_point" ("x" INTEGER NOT NULL , "y" INTEGER NOT NULL );
CREATE TABLE ship_route_waypoint(ship_id INTEGER, warehouse_id INTEGER, waypoint_index INTEGER);
CREATE TABLE ship_route_resources(ship_id INTEGER, waypoint_index INTEGER, res INTEGER, amount INTEGER);
CREATE TABLE 'weapon_storage' ('owner_id' INT, 'weapon_id' INT, 'number' INT, remaining_ticks INT);
CREATE TABLE unit_health ('owner_id' INT, 'health' FLOAT);
CREATE TABLE 'unit' ('type' INTEGER NOT NULL, 'location' INTEGER DEFAULT NULL, 'x' INTEGER DEFAULT NULL, 'y' INTEGER DEFAULT NULL, 'owner' INTEGER NOT NULL);
CREATE TABLE 'component'(worldid INT, name TEXT, module TEXT, class TEXT);
CREATE TABLE bullet(worldid INT, startx INT, starty INT, destx INT, desty INT, speed INT, image TEXT);
CREATE TABLE attacks(remaining_ticks INT, weapon_id INT, damage INT, dest_x INT, dest_y INT);
CREATE TABLE target(worldid INT, target_id INT);
CREATE TABLE diplomacy_allies(player1 INT, player2 INT);
CREATE TABLE diplomacy_enemies(player1 INT, player2 INT);
CREATE TABLE stance(worldid INT, stance TEXT, state TEXT);
CREATE TABLE ship_route(ship_id INTEGER, enabled BOOLEAN, current_waypoint INTEGER, wait_at_load BOOL, wait_at_unload BOOL);
CREATE TABLE ship_route_current_transfer(ship_id INTEGER, res INTEGER, amount INTEGER);
CREATE TABLE "ai_builder" ("building_type" INTEGER NOT NULL , "x" INTEGER NOT NULL , "y" INTEGER NOT NULL , "orientation" INTEGER NOT NULL , "ship" INTEGER);
CREATE TABLE "ai_land_manager" ("owner" INTEGER NOT NULL ,"island" INTEGER NOT NULL ,"feeder_island" BOOL NOT NULL );
CREATE TABLE "ai_land_manager_coords" ("land_manager" INTEGER NOT NULL , "x" INTEGER NOT NULL , "y" INTEGER NOT NULL , "purpose" INTEGER NOT NULL );
CREATE TABLE "ai_mission_domestic_trade" ("source_settlement_manager" INTEGER NOT NULL , "destination_settlement_manager" INTEGER NOT NULL , "ship" INTEGER NOT NULL , "state" INTEGER NOT NULL );
CREATE TABLE "ai_mission_found_settlement" ("land_manager" INTEGER NOT NULL , "ship" INTEGER NOT NULL , "warehouse_builder" INTEGER NOT NULL, "state" INTEGER NOT NULL );
CREATE TABLE "ai_mission_international_trade" ("settlement_manager" INTEGER NOT NULL , "settlement" INTEGER NOT NULL , "ship" INTEGER NOT NULL , "bought_resource" INTEGER, "sold_resource" INTEGER, "state" INTEGER NOT NULL );
CREATE TABLE "ai_mission_prepare_foundation_ship" ("settlement_manager" INTEGER NOT NULL , "ship" INTEGER NOT NULL , "feeder_island" BOOL NOT NULL, "state" INTEGER NOT NULL );
CREATE TABLE "ai_personality_manager" ("personality" TEXT NOT NULL );
CREATE TABLE "ai_player" ("need_more_ships" INTEGER NOT NULL, "need_feeder_island" INTEGER NOT NULL, "remaining_ticks" INTEGER NOT NULL);
CREATE TABLE "ai_production_builder" ("settlement_manager" INTEGER NOT NULL ,"last_collector_improvement_storage" INTEGER NOT NULL ,"last_collector_improvement_road" INTEGER NOT NULL );
CREATE TABLE "ai_production_builder_plan" ("production_builder" INTEGER NOT NULL , "x" INTEGER NOT NULL , "y" INTEGER NOT NULL , "purpose" INTEGER NOT NULL );
CREATE TABLE "ai_resource_manager" ("settlement_manager"  NOT NULL );
CREATE TABLE "ai_resource_manager_requirement" ("resource_manager" INTEGER NOT NULL , "resource" INTEGER NOT NULL , "amount" INTEGER NOT NULL );
CREATE TABLE "ai_resource_manager_trade_storage" ("resource_manager" INTEGER NOT NULL , "settlement_manager" INTEGER NOT NULL , "resource" INTEGER NOT NULL , "amount" DOUBLE NOT NULL );
CREATE TABLE "ai_settlement_manager" ("land_manager" INTEGER NOT NULL );
CREATE TABLE "ai_ship" ("owner" INTEGER NOT NULL ,"state" INTEGER NOT NULL );
CREATE TABLE "ai_single_resource_manager" ("resource_manager" INTEGER NOT NULL , "resource_id" INTEGER NOT NULL , "building_id" INTEGER NOT NULL , "low_priority" DOUBLE NOT NULL, "available" DOUBLE NOT NULL , "total" DOUBLE NOT NULL );
CREATE TABLE "ai_single_resource_manager_quota" ("single_resource_manager" INTEGER NOT NULL ,"identifier" TEXT NOT NULL ,"quota" DOUBLE NOT NULL ,"priority" BOOL NOT NULL );
CREATE TABLE "ai_single_resource_trade_manager" ("trade_manager" INTEGER NOT NULL , "resource_id" INTEGER NOT NULL , "available" DOUBLE NOT NULL , "total" DOUBLE NOT NULL );
CREATE TABLE "ai_single_resource_trade_manager_partner" ("single_resource_trade_manager" INTEGER NOT NULL , "settlement_manager" INTEGER NOT NULL , "amount" DOUBLE NOT NULL );
CREATE TABLE "ai_single_resource_trade_manager_quota" ("single_resource_trade_manager" INTEGER NOT NULL , "identifier" TEXT NOT NULL , "quota" DOUBLE NOT NULL );
CREATE TABLE "ai_trade_manager" ("settlement_manager" INTEGER NOT NULL );
CREATE TABLE "ai_village_builder" ("settlement_manager" INTEGER NOT NULL ,"num_sections" INTEGER NOT NULL ,"current_section" INTEGER NOT NULL );
CREATE TABLE "ai_village_builder_plan" ("village_builder" INTEGER NOT NULL , "x" INTEGER NOT NULL , "y" INTEGER NOT NULL , "purpose" INTEGER NOT NULL , "section" INTEGER, "seq_no" INTEGER);
CREATE TABLE building_collector (home_building INT, creation_tick INT NOT NULL);
CREATE TABLE "building_collector_job_history" ("collector" INTEGER NOT NULL , "tick" INTEGER NOT NULL, "utilisation" FLOAT NOT NULL );
CREATE TABLE "production" ("state" int NOT NULL ,"owner" int,"prod_line_id" int NOT NULL ,"remaining_ticks" int DEFAULT null ,"_pause_old_state" int DEFAULT null ,"creation_tick" INTEGER NOT NULL );
CREATE TABLE "settlement" ("island" INTEGER NOT NULL ,"owner" INTEGER NOT NULL );
CREATE TABLE "settlement_level_properties" ("settlement" INTEGER NOT NULL, "level" INTEGER NOT NULL , "upgrading_allowed" BOOL NOT NULL, "tax_setting" FLOAT NOT NULL);
CREATE TABLE "player" ("color" INTEGER NOT NULL ,"name" TEXT NOT NULL ,"client_id" TEXT,"is_trader" BOOL NOT NULL  DEFAULT (0) ,"is_pirate" BOOL NOT NULL  DEFAULT (0) ,"settler_level" INTEGER NOT NULL ,"difficulty_level" INTEGER);
CREATE TABLE "ai_mission_special_domestic_trade" ("source_settlement_manager" INTEGER NOT NULL , "destination_settlement_manager" INTEGER NOT NULL , "ship" INTEGER NOT NULL , "state" INTEGER NOT NULL );
CREATE TABLE "production_queue" (object INTEGER NOT NULL, position INTEGER NOT NULL, production_line_id INTEGER NOT NULL);
CREATE TABLE production_line(for_worldid INTEGER, type STRING, res INTEGER, amount INTEGER);
CREATE TABLE "resource_overview_bar" (object INTEGER NOT NULL, position INTEGER NOT NULL, resource INTEGER NOT NULL);
CREATE TABLE "settler" ("inhabitants" INTEGER, "last_tax_payed" INTEGER);
CREATE TABLE "settlement_tiles" (data STRING);
CREATE TABLE production_state_history (
    "production" INTEGER NOT NULL,
    "tick" INTEGER NOT NULL,
    "state" INTEGER NOT NULL,
    "object_id" INTEGER NOT NULL
);
CREATE TABLE "trade_history" ("settlement" INTEGER NOT NULL,"tick" INTEGER NOT NULL, "player" INTEGER NOT NULL, "resource_id" INTEGER NOT NULL, "amount" INTEGER NOT NULL, "gold" INTEGER NOT NULL);
CREATE TABLE "disaster" (
	type STRING NOT NULL,
	settlement INTEGER NOT NULL, -- affected settlement
	remaining_ticks_expand INTEGER NOT NULL -- ticks until the disaster will expand next
);
CREATE TABLE "fire_disaster" (
	disaster INTEGER NOT NULL, -- disaster and building together make up the key 
	building INTEGER NOT NULL,
	remaining_ticks_havoc INTEGER NOT NULL
);
CREATE TABLE "disaster_manager" (
	remaining_ticks INTEGER NOT NULL -- manager ticks. will only contain one row.
);

COMMIT;
