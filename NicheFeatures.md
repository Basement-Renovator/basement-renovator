# Niche Features
Some of BR's features are for power users, or aren't very discoverable in the UI. This list attempts to make these neat, but less commonly used features more visible.

### Mirroring Rooms
BR's Duplicate Room feature lets you create exact copies of existing rooms without much effort. However, it's also possible to create an exact mirrored duplicate! This is a pretty common technique for quickly padding out room counts when creating a lot of them, so BR attempts to make this a bit easier. Simply hold Alt and Duplicate will become Mirror (creates a horizontally mirrored duplicate) or Alt+Shift and it will become Mirror Y. (creates a vertically mirrored duplicate) This accounts for directional entities like Grimaces, Wall Huggers, etc. and mirrors them as needed.

### Replace Selected Entities
Sometimes it's desirable to replace a few entities in a room with another one. Simply select these entities and then Alt+Click the replacement entity in the palette and you're done!

### Hooks
While already detailed in the FAQ, this feature lets you run scripts as needed when BR performs various actions. Save hooks run scripts on newly saved stbs, Test hooks run on output xmls before the game launches, etc.

### Export Rooms
Occasionally you may decide to move certain rooms to another file, or want copies there. It would be painstaking to copy them by hand, so BR provides an Export option which lets you select a stb file to copy selected rooms to.

### Better Bulk Replace Entities
Did you know that when bulk replacing entities, the "replaced" entity is based on your currently selected entity in the room, and the "replacement" entity is based on your currently selected entity in the palette? This can save some time when performing this process as you don't have to remember the actual ids. Additionally, leaving the variants and/or subtypes as -1 will either match any, for the replaced entity, or preserve the original value, for the replacement.

### Recompute Room IDs
Ever have a room file where the organization has completely gotten away from you and everything is completely out of order? This fixes that by changing their variants to be in sequence by type, starting with the first one it sees. You can also sort the rooms by variant or name before doing this.

### Turn off custom entities
Sometimes you want BR to open as fast as possible and don't care about mods. For that, set DisableMods to 1 in your settings.ini file in the BR folder.

### Fix libpng warnings
If you're running BR with a console window open, you may notice some warnings from libpng complaining about formats. This is because of issues with how your custom entities icons are saved. To fix these issues and silence the warning, set FixIconFormat to 1 in the settings.ini. It will turn itself off after BR loads mods once, since it shouldn't have any additional work to do.
