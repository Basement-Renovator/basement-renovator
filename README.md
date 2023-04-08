# Basement Renovator

- Basement Renovator is a 3rd-party *[Binding of Isaac: Repentance](https://store.steampowered.com/app/1426300/The_Binding_of_Isaac_Repentance/)* room and level editor.
- It makes it easy to create rooms and is even used by the game's official staff.
- It is open-source and written in [Python 3](https://www.python.org/).
- It was originally written by [Chronometrics](http://www.chronometry.ca/) and is now supported by [budjmt](https://github.com/budjmt).
- It will also edit [Afterbirth+](https://store.steampowered.com/app/570660/The_Binding_of_Isaac_Afterbirth/), [Afterbirth](https://store.steampowered.com/app/401920/The_Binding_of_Isaac_Afterbirth/), and [Rebirth](https://store.steampowered.com/app/250900/The_Binding_of_Isaac_Rebirth/) rooms, but some entity IDs may be incorrect.

### Download

The latest version of Basement Renovator is available in the [releases section](https://github.com/Basement-Renovator/Basement-Renovator/releases), but the program can be run from source if desired.

### Running From Source

* See [INSTALL.md](INSTALL.md#running-from-source).

### How to Create a Mod that Modifies Rooms in the Vanilla Game

- If you're working with Rebirth or Afterbirth, you must use [Rick's Unpacker](http://svn.gib.me/builds/rebirth/) to get STB files. If you are working with the latest version of the game (Afterbirth+ or Repentance), read on.
- First, unpack the game's assets using the official unpacker.
  - On Windows: <br>
  `C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\tools\ResourceExtractor\ResourceExtractor.exe` <br>
  (this will populate the `C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\rooms` directory with .stb files)
  - On MacOS: <br>
  `"$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/tools/ResourceExtractor/ResourceExtractor" "$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources" "$HOME/Documents/IsaacUnpacked"` <br>
  (this will populate the `$HOME/Documents/IsaacUnpacked/resources/rooms` directory with .stb files)
- Now, you can open a floor's STB file using Basement Renovator and change it to your heart's content.
- After saving your work, include the modified STB file in your mod's resources directory (e.g. `C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]\resources`) and it will overwrite the vanilla version of the floor. Note that your mod will be **incompatible** with all other mods that use this technique to replace floors, so this is not recommended.

### How to Create a Mod that Include Extra Rooms

- Use Basement Renovator to create a brand new STB file with only the extra rooms that you want to add. Then, name it with the exact same filename as the vanilla floor STB. (Refer to the previous section if you do not know what the filename is.)
- After saving your work, include the new STB file in your mod's content directory (e.g. `C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]\content\rooms`) and it will add the rooms to the floor.

### How to Use the Interface

- You'll first want to use Basement Renovator to open a vanilla floor STB file in order to look around and get a feel for how it works. Follow the instructions in the "How to Create a Mod that Modifies Rooms in the Vanilla Game" section above. Basement Renovator can read and save them directly, no need to convert to XML.

- **The Editor**: Smack in the middle is the main editor. You can drag any entity in this editor by clicking it, or select multiple entities by dragging a box around them. You can move entities wherever you'd like in the room. You can cut or paste entities, using the menu or keyboard shortcuts, and you can delete them by selecting them and hitting backspace or delete. Alt-click an entity to replace it with the chosen entity in your palette. You can choose whether doors are active or inactive by double clicking them.

- **The Room List**: On the right of the window is the room list dock. This dock is moveable by grabbing the title bar. Click any room in the list to load it into the editor. The type of the room is indicated by the icon to the left of the name, and the ID is the number beside the name. Room type determines the item pool and tileset. Create new rooms by hitting 'add', delete a room by selecting a room and either pressing the backspace/delete key or clicking 'delete', and duplicate a selected room by clicking 'duplicate' (duplicates will have a different variant number).

- **The Room List continued**: Double click a room to change it's name. Mouse over a room to see some info in the tooltip, and right click a room to change the room size, room type, weight (how often it is spawned) and difficulty (how difficult the room is, used to control floor difficulty). Drag and drop rooms in the list to change their position. Use the filters on the top to only show certain rooms. The Export button on the bottom will export all selected rooms to a new STB, or if you choose an existing STB it will append those rooms onto the one you chose.

- **The Entity Palette**: The entity palette on the left is a moveable dock just like the Room List. You can use it to paint entities onto the Editor just like Mario Paint. Simply select an entity from the palette, then right click in the Editor window where you want the entity to paint. You're basically stamping them into the room. All known game entities are listed.
  - When adding, moving, or removing entities, doors will automatically be enabled or disabled based on if entities are in front of them. To override the normal setting, double click the door to toggle its enablement
    - To prevent an entity from blocking doors, give it the `NoBlockDoors` attribute

- **Other Things**: You can show or hide the grid in the edit menu, or by pressing Cmd-G (Ctrl-G on win). You can pick up any of the docks, and move them to new areas, have them as floating windows, or stack them as tabs. There are a few other options in the View menu to give you some choices.

- **Test Menu**: To quickly test your rooms, you can load them from BR directly. You can select multiple rooms to test at a time, or just one. You will be teleported to the right floor for the current file. Here's a summary of the different test methods:
  - Replace Stage
    - Replaces the stage for the current file's rooms with the selected rooms
    - Adds some helpful items and debug commands for each run
    - If the room is skinny or long, (i.e. only two door slots) a padding 1x1 room will be added
    - Note that this method can't replace rooms added by mods to the floor, so they will potentially interfere
  - Replace Starting Room
    - Replaces the global starting room with the currently selected room
    - Does not work with multiple rooms
    - Does not work with skinny rooms, long rooms, and standard L rooms (closets are fine)
  - InstaPreview
    - Opens the game directly into the first room in the selection, skipping all menus
    - Cycle through multiple rooms with `,` and `.`
    - Resetting in a room will move the player to the next door in the room going clockwise
        - Toggle whether to stay at the current door using `;`
        - Invalid doors for the room will be indicated by a red barred door
    - Works most like the base game when testing one room at a time

### F.A.Q.

*The 'InstaPreview' tool isn't working for me; what can I do?*
- Open `settings.ini` in the BR folder in a text editor. Ensure there is a line that says: `InstallFolder=(...)` where (...) is the location of the TBOI install folder containing an executable
 
*How do I edit Repentance rooms?*

- Open `settings.ini` in the BR folder in a text editor. Add a line that says: `CompatibilityMode=Repentance`. Other valid values are `Rebirth`, `Afterbirth`, `Afterbirth+`, and `Antibirth`
- The room files have the same format as AB and AB+

*I found a bug!*

- Please [open an issue on github](https://github.com/Tempus/Basement-Renovator/issues).
- If you need immediate help, many people in the modding community hang out in the **#modding** channel of the [BoI Discord server.](https://discord.gg/isaac)

*When is the next update?*

- There's no formal release schedule. If you want to run BR, it's recommended you follow the steps above to run the mod directly from source. Resources are updated soon after the game updates, so be sure to grab the latest version when that happens!

*Why can't I edit door position? Why can't I make a custom room size?*

- These make the game crash, so they are not included in the editor.

*How do I add custom entities?*

- This will only work for Afterbirth+ mods. Create a folder named `basementrenovator` in your mod's root folder. (It must be within your overall mods folder to be detected.) Inside that folder, create an `EntitiesMod.xml` file. This should use the same format as `resources/EntitiesAfterbirthPlus.xml` and have the same conventions. If `Group` is left out, it will default to `(Mod) Your Mod Name`. The `Image` path is relative to the `basementrenovator` folder within your mod. Finally, BR will only load *enabled* mods to reduce noise and startup time.
- If your entity has some offset from its actual grid location in-game, you can use the `PlaceVisual` attribute. Check `resources/EntitiesAfterbirthPlus` for some examples. It can either be `X,Y` in +/- grid squares of offset or pre-coded dynamic behaviors like `WallSnap`.
  - If you're using this property to add additional visual indicators to your icon or the sprite is asymmetric, you can use `DisableOffsetIndicator` to disable the visual indicator for this offset (only needed if offset is > half a grid)
- When newly placed, grid entities will be placed underneath any regular entities in their stack. To give entities this property, add the `IsGrid` attribute.
- If you have an entity that does not exist in your `entities2.xml` for some reason, you can add `Metadata="1"` to your entity. Be sure you know what you're doing! This suppresses useful error messages and allows BR to load entities it normally wouldn't. (This kind of thing is mostly relevant to helper entities used with [Stage API](https://github.com/Meowlala/BOIStageAPI15))
- If for some reason this is too much hassle, or you want to quickly create rooms with entities from large mods that don't have support, you can toggle the *Autogenerate mod content* setting. This will crawl mods' `content/entities2.xml` instead of the `basementrenovator` folder and work automagically without any additional work. HOWEVER this comes with a number of downsides:
  - It has to generate BR images for every entity in the mod each time the program starts up. This makes it slightly slower, but worse than that is the way the image is selected. For lack of a better technique, the first available frame of the default animation is used. This works fine for many things, but for entities like gapers which have a default body animation with the head as an overlay, the image is very poor compared to a curated one.
  - Entities are classified by Kind automatically, so if you need to specially classify something this won't be smart enough to detect it.
  - Every entity (with a few exceptions like projectiles) the mod adds will show up in BR. All of them. Even the ones that make no sense.
  - The techniques don't mix, and so you'll lose out on the pluses of the other option. For these reasons this setting is not recommended. It's much cleaner to use the `basementrenovator` directory.

*How do I add custom stages?*

- This is very similar to adding custom entities. Create a `basementrenovator` folder and add a file called `StagesMod.xml`. This should use the same format as `resources/StagesAfterbirthPlus.xml` and have the same conventions.
- `BaseGamePath` is an extension-less version of the game's STB file name for that stage. (which most likely does not apply to your modded stage) If not present, a stage will be assumed to be from a mod.
- `BGPrefix` is the path to the backdrop files relative to the `basementrenovator` folder, minus the -.png and -Inner.png for L rooms. If left out, the fallback will be the first stage with the same Stage and StageType with a valid backdrop.
- `Pattern` is the pattern used to match a filename against to determine it's for that stage; if the file contains that prefix it will be set to that stage. The last stage loaded has prefix matching priority, so mods will always have priority over base game stages.
- `Stage` and `StageType` correspond to the in-game enum values for the stage, for modded stages this should point to the stage being replaced.
- `StageHPNum` is an optional value used when calculating the total HP of enemies which use Stage HP. If this is not specified, then `Stage` is used instead.
- Lastly, `Name` is the display name shown in BR, and also passed to room tests to allow for properly replacing the base game stage as needed.

*How do I get some rooms to display different backdrops?*

- Some mods like Revelations add specialized room types, e.g. Chill rooms, where it's helpful to have some kind of visual indicator.
- Create a `basementrenovator` folder and add a file called `RoomTypesMod.xml`. This should use the same format as `resources/RoomTypesAfterbirthPlus.xml` and have the same conventions.
- Entities can also have a child Gfx element following the same format as the RoomTypes file. When this entity is in a room, the backdrop will be overridden to that Gfx
  - If multiple are in the same room, the one with the largest x+y will take priority

*Is there a fast way to set up BR compatibility?*

- You can get a quick and dirty drop-in for your mod's basementrenovator folder by starting up with Autogenerate Mod Content enabled. In BR's resource folder under Entities/ModTemp, there will be a folder with your mod's name.
It will contain an icons folder and an EntitiesMod.xml file. However, this will generate entries for many things you may not want to have entries for, so you'll need to clean it up.
- Some icons may not be what you want out of the box. For example, gapers will be missing their heads because they're overlays, or the first frame might not be a good representative.
BR includes an Icon Generator script under resources to allow for more fine-grained icon generation from any frame in an anm2. Run it with --help or -h for more details.
- This method will not generate custom stages as it's indeterminate how a mod generates them. You'll need to do that step yourself.

*Why does my custom entity appear with a yellow hazard sign on it?*

- While Basement Renovator can save a wide range of values identifying entities, not all of them play nicely in game. Some are fine in game, but are still invalid.
  - Variants are represented in game as 12 bits, which range from 0 - 4095. BR saves them as 32 bit values, and the game can read your modded entity like this, but it will always be reduced into that range. You can be 100% certain of your variant if it falls within that range
  - Ids/Types have the same representation as variants, with an additional twist. Entities of type 1000 or higher are read from rooms as *grid entities* like rocks or spikes. That means your entity will not get spawned in the room at all if its id is that high!
  - Subtypes are represented using 8 bits, or the range 0 - 255. This is the same both in BR and in game. Follows the same rules as variant otherwise.

  If you see this warning, please change your values to fit in the proper range. This will prevent a lot of difficult to debug issues in your mods. You can see exactly where an entity is out of range in the logs or in the tooltip if you hover over it in the room.

*What about a red one?*

- This is because Basement Renovator loaded this entity from one of its own XMLs without finding a matching one in an `entities2.xml` file. That means the type, variant, or subtype in the Basement Renovator XML file is invalid. This is a very dangerous error, as loading a room with an unmatched entity will crash the game when it loads the room! This will take precedence over the yellow hazard sign, but it may have that problem as well. (Check the entity's tooltip for more information)

*What is a hook?*

- Certain work patterns in Basement Renovator require repeatedly taking an outputted file and performing a manual process on it. The most prominent example of this is the AB+ mod [Stage API](https://github.com/Meowlala/BOIStageAPI15) which requires STBs to be converted to Lua files in order for it to properly use them.
- As such a process is error prone and tedious, BR allows users to set up lists of scripts that will be executed on relevant files at various points before it finishes processing them.
  - Save Hook: when a room file is saved, all of these scripts are run with the resulting STB like so: `script.exe "path to file" --save" The bonus --save argument can be used if it's desirable to reuse a single script file.
    - Stage API uses this to convert STBs to Lua files every time you save them
  - Test Hook: when a room is tested, it is output to an XML file. This XML file is passed to a script like so: `script.exe "path to file" --test`
    - Stage API uses this to set up a test room file when testing rooms
- You can add hooks in File > Set Hooks
