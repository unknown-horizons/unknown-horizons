PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

CREATE TABLE "map_properties" (
	"name" TEXT NOT NULL,
	"value" TEXT NOT NULL
);

CREATE TABLE "name" (
	"name" TEXT NOT NULL
);

CREATE TABLE "island" (
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"file" TEXT NOT NULL
);

CREATE TABLE "storage" (
	"object" INT NOT NULL,
	"resource" INT NOT NULL,
	"amount" INT NOT NULL
);

CREATE TABLE "collector_job" (
	"collector" INT,
	"object" INT DEFAULT NULL,
	"resource" INT DEFAULT NULL,
	"amount" INT DEFAULT NULL
);

CREATE TABLE "unit_path" (
	"unit" INT NOT NULL,
	"index" INT NOT NULL,
	"location" INT DEFAULT NULL,
	"x" INT DEFAULT NULL,
	"y" INT DEFAULT NULL
);

CREATE TABLE "metadata" (
	"name" TEXT NOT NULL,
	"value" TEXT DEFAULT ""
);

CREATE TABLE "view" (
	"zoom" REAL NOT NULL,
	"rotation" REAL NOT NULL,
	"location_x" INT NOT NULL,
	"location_y" INT NOT NULL
);

CREATE TABLE "selected" (
	"group" INT,
	"id" INT NOT NULL
);

CREATE TABLE "command" (
	"tick" INT NOT NULL,
	"issuer" INT NOT NULL,
	"data" TEXT NOT NULL 
);

CREATE TABLE "building" (
	"type" INT,
	"x" INT,
	"y" INT,
	"location" INT,
	"rotation" INT,
	"level" INT NOT NULL DEFAULT 0
);

CREATE TABLE "storage_properties" (
	"object" INT NOT NULL,
	"name" TEXT NOT NULL,
	"value" TEXT
);

CREATE TABLE "trade_buy" (
	"object" INT NOT NULL,
	"resource" INT NOT NULL,
	"trade_limit" INT NOT NULL
);

CREATE TABLE "trade_sell" (
	"object" INT NOT NULL,
	"resource" INT NOT NULL,
	"trade_limit" INT NOT NULL
);

CREATE TABLE "collector" (
	"state" INT NOT NULL,
	"remaining_ticks" INT,
	"start_hidden" BOOL NOT NULL DEFAULT '1'
);

CREATE TABLE "trader_ships" (
	"state" INT NOT NULL,
	"remaining_ticks" INT,
	"targeted_warehouse" INT
);

CREATE TABLE "wildanimal" (
	"can_reproduce" BOOL,
	"health" INT
);

CREATE TABLE "message_widget_active" (
	"id" INT NOT NULL,
	"read" INT NOT NULL,
	"created" INT NOT NULL,
	"display" INT NOT NULL,
	"message" TEXT NOT NULL DEFAULT "",
	"x" INT,
	"y" INT
);

CREATE TABLE "message_widget_archive" (
	"id" INT NOT NULL,
	"read" INT NOT NULL,
	"created" INT NOT NULL,
	"display" INT NOT NULL,
	"message" TEXT NOT NULL DEFAULT "",
	"x" INT,
	"y" INT
);

CREATE TABLE "concrete_object" (
	"id" INT,
	"action_runtime" INT,
	"action_set_id" TEXT
);

CREATE TABLE "metadata_blob" (
	"name" TEXT NOT NULL,
	"value" BLOB
);

CREATE TABLE "pirate_ships" (
	"state" INT NOT NULL DEFAULT 0,
	"remaining_ticks" INT DEFAULT 0
);

CREATE TABLE "storage_global_limit" (
	"object" INT NOT NULL,
	"value" INT NOT NULL
);

CREATE TABLE "scenario_variables" (
	"key" TEXT NOT NULL,
	"value" TEXT NOT NULL 
);

CREATE TABLE "logbook" (
	"widgets" TEXT
);

CREATE TABLE "logbook_messages" (
	"message" TEXT,
	"displayed" BOOL
);

CREATE TABLE "trade_values" (
	"object" INT NOT NULL,
	"total_income" INT NOT NULL,
	"total_expenses" INT NOT NULL 
);

CREATE TABLE "mine" (
	"deposit_class" INT NOT NULL,
	"mine_empty_msg_shown" BOOL
);

CREATE TABLE "settlement_produced_res" (
	"settlement" INT NOT NULL,
	"res" INT NOT NULL,
	"amount" INT NOT NULL
);

CREATE TABLE "remaining_ticks_of_month" (
	"ticks" INT
);

CREATE TABLE "pirate_home_point" (
	"x" INT NOT NULL,
	"y" INT NOT NULL 
);

CREATE TABLE "ship_route_waypoint" (
	"ship_id" INT,
	"warehouse_id" INT,
	"waypoint_index" INT
);

CREATE TABLE "ship_route_resources" (
	"ship_id" INT,
	"waypoint_index" INT,
	"res" INT,
	"amount" INT
);

CREATE TABLE "weapon_storage" (
	"owner_id" INT,
	"weapon_id" INT,
	"number" INT,
	"remaining_ticks" INT
);

CREATE TABLE "unit_health" (
	"owner_id" INT,
	"health" REAL
);

CREATE TABLE "unit" (
	"type" INT NOT NULL,
	"location" INT DEFAULT NULL,
	"x" INT DEFAULT NULL,
	"y" INT DEFAULT NULL,
	"owner" INT NOT NULL
);

CREATE TABLE "bullet" (
	"worldid" INT,
	"startx" INT,
	"starty" INT,
	"destx" INT,
	"desty" INT,
	"speed" INT,
	"image" TEXT
);

CREATE TABLE "attacks" (
	"remaining_ticks" INT,
	"weapon_id" INT,
	"damage" INT,
	"dest_x" INT,
	"dest_y" INT
);

CREATE TABLE "target" (
	"worldid" INT,
	"target_id" INT
);

CREATE TABLE "diplomacy_allies" (
	"player1" INT,
	"player2" INT
);

CREATE TABLE "diplomacy_enemies" (
	"player1" INT,
	"player2" INT
);

CREATE TABLE "stance" (
	"worldid" INT,
	"stance" TEXT,
	"state" TEXT
);

CREATE TABLE "ship_route" (
	"ship_id" INT,
	"enabled" BOOL,
	"current_waypoint" INT,
	"wait_at_load" BOOL,
	"wait_at_unload" BOOL
);

CREATE TABLE "ship_route_current_transfer" (
	"ship_id" INT,
	"res" INT,
	"amount" INT
);

CREATE TABLE "ai_builder" (
	"building_type" INT NOT NULL,
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"orientation" INT NOT NULL,
	"ship" INT
);

CREATE TABLE "ai_land_manager" (
	"owner" INT NOT NULL,
	"island" INT NOT NULL,
	"feeder_island" BOOL NOT NULL 
);

CREATE TABLE "ai_land_manager_coords" (
	"land_manager" INT NOT NULL,
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"purpose" INT NOT NULL 
);

CREATE TABLE "ai_mission_domestic_trade" (
	"source_settlement_manager" INT NOT NULL,
	"destination_settlement_manager" INT NOT NULL,
	"ship" INT NOT NULL,
	"state" INT NOT NULL 
);

CREATE TABLE "ai_mission_found_settlement" (
	"land_manager" INT NOT NULL,
	"ship" INT NOT NULL,
	"warehouse_builder" INT NOT NULL,
	"state" INT NOT NULL 
);

CREATE TABLE "ai_mission_international_trade" (
	"settlement_manager" INT NOT NULL,
	"settlement" INT NOT NULL,
	"ship" INT NOT NULL,
	"bought_resource" INT,
	"sold_resource" INT,
	"state" INT NOT NULL 
);

CREATE TABLE "ai_mission_prepare_foundation_ship" (
	"settlement_manager" INT NOT NULL,
	"ship" INT NOT NULL,
	"feeder_island" BOOL NOT NULL,
	"state" INT NOT NULL 
);

CREATE TABLE "ai_personality_manager" (
	"personality" TEXT NOT NULL 
);

CREATE TABLE "ai_player" (
	"need_more_ships" INT NOT NULL,
	"need_more_combat_ships" INTEGER NOT NULL DEFAULT 1,
	"need_feeder_island" INT NOT NULL,
	"remaining_ticks" INT NOT NULL,
	"remaining_ticks_long" INTEGER NOT NULL
);

CREATE TABLE "ai_pirate" (
	"remaining_ticks" INTEGER NOT NULL DEFAULT 1,
	"remaining_ticks_long" INTEGER NOT NULL
);

CREATE TABLE "ai_production_builder" (
	"settlement_manager" INT NOT NULL,
	"last_collector_improvement_storage" INT NOT NULL,
	"last_collector_improvement_road" INT NOT NULL 
);

CREATE TABLE "ai_production_builder_plan" (
	"production_builder" INT NOT NULL,
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"purpose" INT NOT NULL 
);

CREATE TABLE "ai_resource_manager" (
	"settlement_manager"  NOT NULL 
);

CREATE TABLE "ai_resource_manager_requirement" (
	"resource_manager" INT NOT NULL,
	"resource" INT NOT NULL,
	"amount" INT NOT NULL 
);

CREATE TABLE "ai_resource_manager_trade_storage" (
	"resource_manager" INT NOT NULL,
	"settlement_manager" INT NOT NULL,
	"resource" INT NOT NULL,
	"amount" REAL NOT NULL 
);

CREATE TABLE "ai_settlement_manager" (
	"land_manager" INT NOT NULL 
);

CREATE TABLE "ai_ship" (
	"owner" INT NOT NULL,
	"state" INT NOT NULL 
);

CREATE TABLE "fleet" (
	"fleet_id" INTEGER NOT NULL,
	"owner_id" INTEGER NOT NULL,
	"state_id" INTEGER NOT NULL,
	"dest_x" INTEGER, "dest_y" INTEGER,
	"radius" INTEGER, "ratio" DOUBLE
);

CREATE TABLE "fleet_ship" (
	"fleet_id" INTEGER NOT NULL,
	"ship_id" INTEGER NOT NULL,
	"state_id" INTEGER NOT NULL
);

CREATE TABLE "ai_behavior_manager" (
	"owner_id" INTEGER NOT NULL,
	"profile_token" INTEGER NOT NULL
);

CREATE TABLE "ai_combat_ship" (
	"owner_id" INTEGER NOT NULL,
	"ship_id" INTEGER NOT NULL,
	"state_id" INTEGER NOT NULL
);

CREATE TABLE "ai_fleet_mission" (
	"owner_id" INTEGER NOT NULL,
	"fleet_id" INTEGER NOT NULL,
	"state_id" INTEGER NOT NULL,
	"combat_phase" BOOL NOT NULL
);

CREATE TABLE "ai_scouting_mission" (
	"target_point_x" INTEGER NOT NULL,
	"target_point_y" INTEGER NOT NULL,
	"starting_point_x" INTEGER NOT NULL,
	"starting_point_y" INTEGER NOT NULL
);

CREATE TABLE "ai_mission_surprise_attack" (
	"enemy_player_id" INTEGER NOT NULL,
	"target_point_x" INTEGER NOT NULL,
	"target_point_y" INTEGER NOT NULL,
	"target_point_radius" INTEGER NOT NULL,
	"return_point_x" INTEGER NOT NULL,
	"return_point_y" INTEGER NOT NULL
);

CREATE TABLE "ai_mission_chase_ships_and_attack" (
	"target_ship_id" INTEGER NOT NULL
);

CREATE TABLE "ai_mission_pirate_routine" (
	"target_point_x" INTEGER NOT NULL,
	"target_point_y" INTEGER NOT NULL
);

CREATE TABLE "ai_condition_lock" (
	"owner_id" INTEGER NOT NULL,
	"condition" TEXT NOT NULL,
	"mission_id" INTEGER NOT NULL
);

CREATE TABLE "ai_single_resource_manager" (
	"resource_manager" INT NOT NULL,
	"resource_id" INT NOT NULL,
	"building_id" INT NOT NULL,
	"low_priority" REAL NOT NULL,
	"available" REAL NOT NULL,
	"total" REAL NOT NULL 
);

CREATE TABLE "ai_single_resource_manager_quota" (
	"single_resource_manager" INT NOT NULL,
	"identifier" TEXT NOT NULL,
	"quota" REAL NOT NULL,
	"priority" BOOL NOT NULL 
);

CREATE TABLE "ai_single_resource_trade_manager" (
	"trade_manager" INT NOT NULL,
	"resource_id" INT NOT NULL,
	"available" REAL NOT NULL,
	"total" REAL NOT NULL 
);

CREATE TABLE "ai_single_resource_trade_manager_partner" (
	"single_resource_trade_manager" INT NOT NULL,
	"settlement_manager" INT NOT NULL,
	"amount" REAL NOT NULL 
);

CREATE TABLE "ai_single_resource_trade_manager_quota" (
	"single_resource_trade_manager" INT NOT NULL,
	"identifier" TEXT NOT NULL,
	"quota" REAL NOT NULL 
);

CREATE TABLE "ai_trade_manager" (
	"settlement_manager" INT NOT NULL 
);

CREATE TABLE "ai_village_builder" (
	"settlement_manager" INT NOT NULL,
	"num_sections" INT NOT NULL,
	"current_section" INT NOT NULL 
);

CREATE TABLE "ai_village_builder_plan" (
	"village_builder" INT NOT NULL,
	"x" INT NOT NULL,
	"y" INT NOT NULL,
	"purpose" INT NOT NULL,
	"section" INT,
	"seq_no" INT
);

CREATE TABLE "building_collector" (
	"home_building" INT,
	"creation_tick" INT NOT NULL
);

CREATE TABLE "building_collector_job_history" (
	"collector" INT NOT NULL,
	"tick" INT NOT NULL,
	"utilisation" REAL NOT NULL 
);

CREATE TABLE "production" (
	"state" INT NOT NULL,
	"owner" INT,
	"prod_line_id" INT NOT NULL,
	"remaining_ticks" INT DEFAULT NULL,
	"_pause_old_state" INT DEFAULT NULL,
	"creation_tick" INT NOT NULL 
);

CREATE TABLE "settlement" (
	"island" INT NOT NULL,
	"owner" INT NOT NULL 
);

CREATE TABLE "settlement_level_properties" (
	"settlement" INT NOT NULL,
	"level" INT NOT NULL,
	"upgrading_allowed" BOOL NOT NULL,
	"tax_setting" REAL NOT NULL
);

CREATE TABLE "player" (
	"color" INT NOT NULL,
	"name" TEXT NOT NULL,
	"client_id" TEXT,
	"is_trader" BOOL NOT NULL DEFAULT (0),
	"is_pirate" BOOL NOT NULL DEFAULT (0),
	"settler_level" INT NOT NULL,
	"difficulty_level" INT
);

CREATE TABLE "ai_mission_special_domestic_trade" (
	"source_settlement_manager" INT NOT NULL,
	"destination_settlement_manager" INT NOT NULL,
	"ship" INT NOT NULL,
	"state" INT NOT NULL 
);

CREATE TABLE "production_queue" (
	"object" INT NOT NULL,
	"position" INT NOT NULL,
	"production_line_id" INT NOT NULL
);

CREATE TABLE "production_line" (
	"for_worldid" INT,
	"type" TEXT,
	"res" INT,
	"amount" INT
);

CREATE TABLE "resource_overview_bar" (
	"object" INT NOT NULL,
	"position" INT NOT NULL,
	"resource" INT NOT NULL
);

CREATE TABLE "settler" (
	"inhabitants" INT,
	"last_tax_payed" INT
);

CREATE TABLE "settlement_tiles" (
	"data" TEXT
);

CREATE TABLE "production_state_history" (
	"production" INT NOT NULL,
	"tick" INT NOT NULL,
	"state" INT NOT NULL,
	"object_id" INT NOT NULL
);

CREATE TABLE "trade_history" (
	"settlement" INT NOT NULL,
	"tick" INT NOT NULL,
	"player" INT NOT NULL,
	"resource_id" INT NOT NULL,
	"amount" INT NOT NULL,
	"gold" INT NOT NULL
);

CREATE TABLE "disaster" (
	"type" TEXT NOT NULL,
	"settlement" INT NOT NULL, -- affected settlement
	"remaining_ticks_expand" INT NOT NULL -- ticks until the disaster will expand next
);

CREATE TABLE "fire_disaster" (
	"disaster" INT NOT NULL, -- disaster and building together make up the key 
	"building" INT NOT NULL,
	"remaining_ticks_havoc" INT NOT NULL
);

CREATE TABLE "disaster_manager" (
	"remaining_ticks" INT NOT NULL -- manager ticks. will only contain one row.
);

CREATE TABLE "last_active_settlement" (
	"type" TEXT NOT NULL,
	"value" INT NOT NULL
);


COMMIT;
