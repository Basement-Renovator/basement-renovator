# Basement Renovator

* Basement Renovator is a 3rd-party *[Binding of Isaac: Rebirth](https://store.steampowered.com/app/250900/The_Binding_of_Isaac_Rebirth/)* room and level editor.
* It is open-source and written in [Python 3](https://www.python.org/).
* It is much better than the room editor included with the game and is even used by the official staff to create new content.
* It was originally written by [Colin Naga](http://www.chronometry.ca/) and is now supported by the modding community.

### Compatibility

The current version will work on floor files for the *[Afterbirth](https://store.steampowered.com/app/401920/The_Binding_of_Isaac_Afterbirth/)* expansion and the *[Afterbirth+](https://store.steampowered.com/app/570660/The_Binding_of_Isaac_Afterbirth/)* expansion, but not for the base game (*Rebirth*). If you need to edit *Rebirth* floors for some reason, just use an [older version of the code](https://github.com/Tempus/Basement-Renovator/tree/a952cd030b0bf677e07a874ea7be901242a6505c)

### Downloads

There are some older packaged downloads that are on the [releases tab](https://github.com/Tempus/Basement-Renovator/releases), but these are **out of date**. Please run Basement Renovator from source.

### Running from Source (Windows)

Perform the following steps in an **an elevated (administrator) command-shell**.

* Install [Chocolatey](https://chocolatey.org/):
  * `@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"`
* Install [Git](https://git-scm.com/) and [Python 3](https://www.python.org/):
  * `choco install git python3 -y`
  * `refreshenv`
* Install the Python dependencies:
  * `pip install pyqt5 psutil`
* Clone the repository:
  * `cd %userprofile%\Documents` <br />
  (or wherever you want the repository to live) 
  * `git clone https://github.com/Tempus/Basement-Renovator.git` <br />
  (or clone a fork, if you are doing development work)
* Run it:
  * `cd Basement-Renovator`
  * `python BasementRenovator.py`

### Running from Source (macOS)

Perform the following steps in Terminal.

* Install [brew](https://brew.sh/):
  * `/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`
* Install [Python 3](https://www.python.org/):
  * `brew install python`
* Install the Python dependencies:
  * `pip3 install pyqt5 psutil`
* Clone the repository:
  * `cd ~/Documents/` <br />
  (or wherever you want the repository to live) 
  * `git clone https://github.com/Tempus/Basement-Renovator.git` <br />
  (or clone a fork, if you are doing development work)
* Run it:
  * `cd Basement-Renovator`
  * `python3 BasementRenovator.py`

### How to Create a Mod that Modifies Rooms in the Vanilla Game

* First, unpack the game's assets using the official unpacker.
  * On Windows: `C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\tools\ResourceExtractor\ResourceExtractor.exe` <br />
  (this will populate the "C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\rooms" directory with .stb files)
  (on Windows)
  * On MacOS: `"$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/tools/ResourceExtractor/ResourceExtractor" "$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources" "$HOME/Documents/IsaacUnpacked"` <br />
  (this will populate the "$HOME/Documents/IsaacUnpacked/resources/rooms" directory with .stb files)
* Now, you can open a floor's STB file using Basement Renovator and change it to your heart's content.
* After saving your work, include the modified STB file in your mod's resources directory (e.g. "C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]\resources" and it will overwrite the vanilla version of the floor. Note that your mod will be **incompatible** with all other mods that use this technique to replace floors, so this is not recommended. 

### How to Create a Mod that Include Extra Rooms

* Use Basement Renovator to create a brand new STB file with only the extra rooms that you want to add. Then, name it with the exact same filename as the vanilla floor STB. (Refer to the previous section if you do not know what the filename is.)
* After saving your work, include the new STB file in your mod's content directory (e.g. "C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]\content\rooms" and it will add the rooms to the floor.

### How to Use the Interface

* You will first want to use Basement Renovator to open a vanilla floor STB file in order to look around and get a feel for how it works. Follow the instructions in the "How to Create a Mod that Modifies Rooms in the Vanilla Game" section above.

* **The Editor**: Smack in the middle is the main editor. You can drag any entity in this editor by clicking it, or select multiple entities by dragging a box around them. You can move entities wherever you'd like in the room. You can cut or paste entities, using the menu or keyboard shortcuts, and you can delete them by selecting them and hitting backspace or delete. Alt-click an entity to replace it with the chosen entity in your palette. You can choose whether doors are active or inactive by double clicking them.

* **The Room List**: On the right of the window is the room list dock. This dock is moveable by grabbing the titlebar. Click any room in the list to load it into the editor. The type of the room is indicated by the icon to the left of the name, and the ID is the number beside the name. Room type determines the item pool and tileset. Create new rooms by hitting 'add', delete a room by selecting a room and either pressing the backspace/delete key or clicking 'delete', and duplicate a selected room by clicking 'duplicate' (duplicates will have a different variant number). 

* **The Room List continued**: Double click a room to change it's name. Mouse over a room to see some info in the tooltip, and right click a room to change the room size, room type, weight (how often it is spawned) and difficulty (how difficult the room is, used to control floor difficulty). Drag and drop rooms in the list to change their position. Use the filters on the top to only show certain rooms. The Export button on the bottom will export all selected rooms to a new stb, or if you choose an existing stb it will append those rooms onto the one you chose.

* **The Entity Palette**: The entity palette on the left is a moveable dock just like the Room List. You can use it to paint entities onto the Editor just like Mario Paint. Simply select an entity from the palette, then right click in the Editor window where you want the entity to paint. You're basically stamping them into the room. All known game entities are listed.

* **Other Things**: You can show or hide the grid in the edit menu, or by pressing Cmd-G (Ctrl-G on win). You can pick up any of the docks, and move them to new areas, have them as floating windows, or stack them as tabs. There are a few other options in the View menu to give you some choices.

* **Test Menu**: There's a really useful test feature in the menu bar. You can load up rooms to test easily anywhere in the Basement/Cellar, or in the start room directly. The start room only supports 1x1 rooms, however! Makes testing a breeze.

### Community & Help

* If you find a bug or an issue, you can [open an issue](https://github.com/Tempus/Basement-Renovator/issues).
* Many people in the modding community hang out in the #modding channel of the [BoI Discord server](https://discord.gg/isaac).
