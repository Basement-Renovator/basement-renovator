# Niche Features
Some of BR's features are for power users, or aren't very discoverable in the UI. This list attempts to make these neat, but less commonly used features more visible.

### Mirroring Rooms
BR's Duplicate Room feature lets you create exact copies of existing rooms without much effort. However, it's also possible to create an exact mirrored duplicate! This is a pretty common technique for quickly padding out room counts when creating a lot of them, so BR attempts to make this a bit easier. Simply hold Alt and Duplicate will become Mirror (creates a horizontally mirrored duplicate) or Alt+Shift and it will become Mirror Y. (creates a vertically mirrored duplicate) This accounts for directional entities like Grimaces, Wall Huggers, etc. and mirrors them as needed. You can support this for your own entities via the MirrorX and MirrorY attributes. See BR's Entities xml for examples.

### Entity Palette Bonuses

#### Replace Selected Entities
Sometimes it's desirable to replace a few entities in a room with another one. Simply select these entities and then Alt+Click the replacement entity in the palette and you're done!

#### Keep Current Filter, Select a new Paint Entity
Sometimes you'd like to keep an entity filter active while selecting new entities to paint for the current room. Ctrl+Click the entity you'd like to paint and the current entity filter will not change.
You can also invert the normal behavior by toggling Edit > Pin Entity Filter.

#### Place Multiple Entities With Matching Attributes
Sometimes it's desirable to place an entity with all the same attributes of another. Selecting an entity in-room that matches the one you have selected in the palette will do this automatically!

### Filter by other properties
If you'd like to filter rooms by things other than entities, type, and size, you can filter for other room properties through the *Other* filter. This includes properties like weight, difficulty, subtype, and the last time the room was tested.
  - As an aside, last test time is filtered differently from other properties.
  - If no range is used, rooms that have never been tested or were tested before the left time are included.
  - If a range is used, only rooms tested between the times are included, starting with the right time and ending with the left.

### Hooks
While already detailed in the FAQ, this feature lets you run scripts as needed when BR performs various actions. Save hooks run scripts on newly saved stbs, Test hooks run on output xmls before the game launches, etc.

### Copy Rooms to Another File
Occasionally you may decide to move certain rooms to another file, or want copies there. It would be painstaking to copy them by hand, so BR provides an `Copy to File` option which lets you select a room file to copy selected rooms to.

### Better Bulk Replace Entities
Did you know that when bulk replacing entities, the "replaced" entity is based on your currently selected entity in the room, and the "replacement" entity is based on your currently selected entity in the palette? This can save some time when performing this process as you don't have to remember the actual ids. Additionally, leaving the variants and/or subtypes as -1 will either match any, for the replaced entity, or preserve the original value, for the replacement.

In the event of replacing entities across many files, check out the `bulk-entity-replacer` script in `src`. Given a config file specifying replaced entities and files to operate on, this will replace entities across those files.

### Entities with SubType Properties
Some entities (e.g. Ball & Chain and Fissure Spawner) use their SubType to customize their behavior, rather than using it as another variant (e.g. pickups). Middle-click entities to access these customizable properties.

### Recompute Room IDs
Ever have a room file where the organization has completely gotten away from you and everything is completely out of order? This fixes that by changing their variants to be in sequence by type, starting with the first one it sees. You can also sort the rooms by variant or name before doing this.

### Find Empty Rooms
Hypothetically you've created a bunch of rooms with... nothing in them. You did this as part of a placeholder comedic naming scheme involving a certain rapping community member, perhaps. Well now you need to figure out which ones still need attention, but fear not. If you filter for the "Null" room type, since the type isn't used much normally the filter will also include "empty" rooms. The rooms can contain a few harmless entities, like decorations and cobwebs. You can add your own entities with the 'InEmptyRooms' attribute.

### Turn off custom entities
Sometimes you want BR to open as fast as possible and don't care about mods. For that, set DisableMods to 1 in your settings.ini file in the BR folder.

### Fix libpng warnings
If you're running BR with a console window open, you may notice some warnings from libpng complaining about formats. This is because of issues with how your custom entities icons are saved. To fix these issues and silence the warning, set FixIconFormat to 1 in the settings.ini. It will turn itself off after BR loads mods once, since it shouldn't have any additional work to do.

### DRM Free Isaac
There is some subset of users who are using DRM free copies of Isaac, or test builds not through Steam. The test launcher uses Steam directly to avoid an annoying popup, but if the Isaac exe is DRM free launching through Steam is unintended behavior and undesired. To disable trying to launch Isaac through steam, set `ForceExeLaunch` to 1 in your settings.ini.

### Permissions Issues while Testing
There is some subset of users who have found that the normal test launch method for InstaPreview is rejected by their OS. To get around this, set `ForceUrlLaunch` to 1 in your settings.ini.

### Test Antibirth
Anitbirth is capable of Instapreview testing for goofing around. In the absence of a true compatibility mode, you can quickly test rooms for poking its behavior. To test rooms in Anti, go to `settings.ini` and set `AntibirthPath` to the folder you have Antibirth installed in (formatted like `InstallPath`) and set `CompatibilityMode` to `Antibirth`. This only supports Instapreview. For Antibirth enemies, check out `resources/EntitiesAntibirth.xml`. Icon PRs welcome!
