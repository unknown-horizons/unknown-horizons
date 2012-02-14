# Open Editor Tasks/Problems #


## Saving Buildings ##

Since buildings now require a lot of stuff in a lot of DB tables for each of their
components, buildings can be saved to the map, but the maps cannot be opened in
the game.

### Possible Solution ###
To accomplish this, each component could implement a method to save a vanilla object
to the database. Then the necessary components could be read from the YAML file and
for each the necessary entries in the DB could be created correctly.


## Rotated Buildings Move on Save ##

The buildings are rotated correctly in the Editor when loaded. Since the rotation code
adjusts the position of the buildings when they are not in standard rotation, they are
saved with a different position each time the map is saved (they sort of wander in a
diagonal across the map).

### Possible Solution ###
Either there must be an inverse function for the rotation to correct the movement or
the offset of the rotation must be remembered for each building.


## Rotating Buildings in the Editor ##

The editor provides methods to rotate buildings, but since UH handles this much differently
than FIFE, this does not do anything at all.

### Possible Solution ###
Either fix this somehow (not sure how) or build a new interface for rotation. Both is
very time consuming.

