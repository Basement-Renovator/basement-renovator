# **Basement Renovator** ***v2.0rc1***
##### *A Binding of Isaac Afterbirth Level Editor*
---

Hello everyone! Today marks the release of version 1.0 of the Basement Renovator! The Basement Renovator is an easy to use, intuitive tool for editing The Binding of Isaac Afterbirth rooms. It will *not*, I repeat, will *not* edit Rebirth rooms.

This is the first *release candidate*. It has only been tested on a few other computers, so chances are some of you may have crashes on load. Be warned!

### Downloads

[Basement Renovator v2.0rc1 - for Windows](https://github.com/Tempus/Basement-Renovator/releases/download/2.0rc1/Basement.Renovator.zip)

[Basement Renovator v2.0rc1 (Github Source)](https://github.com/Tempus/Basement-Renovator)

### Installation

To run on Windows, download the Windows release and double click the binary.

To run from source (Win, OSX, or Linux), install Python 3.x and PyQt5, then run BasementRenovatorAfterbirth.py from the terminal. 

## *Mac (One time setup):*

* [Download the source](https://github.com/Tempus/Basement-Renovator/archive/master.zip) from the git
* Open a terminal
* [Install Homebrew](http://brew.sh) via the one line terminal script at the bottom of the page
* Type 'brew install python3.5' in the Terminal, wait until it finishes
* Type 'brew install pyqt5' in the Terminal, wait until it finishes
* Type 'python3.5 ' (with the space) in the Terminal, then drag BasementRenovator.py onto the Terminal window, and hit enter

---

### Major New Features for version 2.0

* **Full Afterbirth support** has been added, including all entities and the new room sizes
* New Info text on the screen displays current room and selected entity information
* Filter and **search by name or room ID**
* Room ID now shows beside the name
* Better saving feedback and dirty notification
* **Auto-testing function** takes the drudgery out of room testing
* Wide array of minor fixes and improvements

---

### How to Use

* **STB Files**: You can get .stb files for editing via [Rick's Unpacker](http://svn.gib.me/builds/rebirth/). Once you've extracted them from the game files, Basement Renovator can read and save them directly, no need to convert to XML.

* **The Editor**: Smack in the middle is the main editor. You can drag any entity in this editor by clicking it, or select multiple entities by dragging a box around them. You can move entities wherever you'd like in the room. You can cut or paste entities, using the menu or keyboard shortcuts, and you can delete them by selecting them and hitting backspace or delete. Alt-click an entity to replace it with the chosen entity in your palette. You can choose whether doors are active or inactive by double clicking them.

* **The Room List**: On the right of the window is the room list dock. This dock is moveable by grabbing the titlebar. Click any room in the list to load it into the editor. The type of the room is indicated by the icon to the left of the name, and the ID is the number beside the name. Room type determines the item pool and tileset. Create new rooms by hitting 'add', delete a room by selecting a room and either pressing the backspace/delete key or clicking 'delete', and duplicate a selected room by clicking 'duplicate' (duplicates will have a different variant number). 

* **The Room List cont.**: Double click a room to change it's name. Mouse over a room to see some info in the tooltip, and right click a room to change the room size, room type, weight (how often it is spawned) and difficulty (how difficult the room is, used to control floor difficulty). Drag and drop rooms in the list to change their position. Use the filters on the top to only show certain rooms. The Export button on the bottom will export all selected rooms to a new stb, or if you choose an existing stb it will append those rooms onto the one you chose.

* **The Entity Palette**: The entity palette on the left is a moveable dock just like the Room List. You can use it to paint entities onto the Editor just like Mario Paint. Simply select an entity from the palette, then right click in the Editor window where you want the entity to paint. You're basically stamping them into the room. All known game entities are listed.

* **Other Things**: You can show or hide the grid in the edit menu, or by pressing Cmd-G (Ctrl-G on win). You can pick up any of the docks, and move them to new areas, have them as floating windows, or stack them as tabs. There are a few other options in the View menu to give you some choices.

* **Test Menu**: There's a really useful new Test feature in the menu bar. You can load up rooms to test easily anywhere in the Basement/Cellar, or in the start room directly. The start room only supports 1x1 rooms, however! You must be running the legal steam version of BoI:Afterbirth to use this feature. Makes testing a breeze.

---

### F.A.Q.

*I found a bug!*

- Please report it in the comments, or [open an issue on github](https://github.com/Tempus/Basement-Renovator/issues) (which I will check for the couple weeks before forgetting it exists again). 

*I found something new you don't have!*

- If there's something I missed, that counts as a bug. Let me know!

*When is the next update?*

- I'm pretty damned busy these days. I'm pulling 60-80 hours a week, and I've got other, relaxing hobbies I want to engage in as well. I'll push the release version within the month, depending on the severity or reported bugs.

*Why can't I edit door position/custom room size/make random entities?*

- All of these have no effect, make the game buggy, or crash, and are not included in this editor.

*Where is custom entity support?*

- Due to a number of considerations, including Afterbirth+, I'm shelving this for now. You can add custom entities pretty easily though: just add a new entry to your own EntitiesAfterbirth.xml and voila! Custom entity. Open the 'resources/EntitiesAfterbirth.xml' in any quality text editor (like Notepad++ or Sublime Text), and add a new entry just like the many that already exist there.
