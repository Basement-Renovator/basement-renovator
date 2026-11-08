<span>[ <a href="README.md">English</a> | 中文 ]</span>
# 地下室编辑器（Basement Renovator）

- 地下室编辑器（Basement Renovator）是一款用于 *[《以撒的结合：忏悔》（The Binding of Isaac: Repentance）](https://store.steampowered.com/app/1426300/The_Binding_of_Isaac_Repentance/)* 的第三方房间和楼层编辑器。
  - 它也支持编辑 [《胎衣+》（Afterbirth+）](https://store.steampowered.com/app/570660/The_Binding_of_Isaac_Afterbirth/)、[《胎衣》（Afterbirth）](https://store.steampowered.com/app/401920/The_Binding_of_Isaac_Afterbirth/) 和 [《重生》（Rebirth）](https://store.steampowered.com/app/250900/The_Binding_of_Isaac_Rebirth/) 版本的房间。
- 它让房间制作更加轻松，甚至游戏官方团队也在使用。
- 本项目开源，使用 [Python 3](https://www.python.org/) 编写。
- 最初由 [Chronometrics](http://www.chronometry.ca/) 开发，目前由 [budjmt](https://github.com/budjmt) 维护。

### 下载

你可以从 GitHub 的 [版本发布页面](https://github.com/Basement-Renovator/Basement-Renovator/releases) 下载 Basement Renovator 的最新版本，也可以直接从源码运行程序。

### 从源码运行

- 请参阅 [INSTALL.md](INSTALL.md#running-from-source)。

### 如何查看原版游戏的房间

- 如果使用的是《重生》（Rebirth）或《胎衣》（Afterbirth），需要使用 [Rick's Unpacker](http://svn.gib.me/builds/rebirth/) 获取 STB 文件。如果使用的是较新的版本——《胎衣+》（Afterbirth+）、《忏悔》（Repentance）或《忏悔+》（Repentance+）——请继续按照以下步骤操作。
- 首先，使用游戏自带的官方解包工具提取资源。
  - **Windows：** <br>
    `[TBOI Install Folder]\tools\ResourceExtractor\ResourceExtractor.exe` <br>
    其中，`[TBOI Install Folder]` 表示《以撒的结合》的游戏安装目录。运行解包程序后，`.stb` 文件会被提取到 `[TBOI Install Folder]\resources\rooms`；对于《忏悔+》（Repentance+），提取路径则为 `[TBOI Install Folder]\extracted_resources\resources\rooms`。
    - 从《忏悔+》（Repentance+）开始，需要先将 `ResourceExtractor.exe` 和 `filelist.txt` 复制到游戏安装目录，再双击运行解包程序。
  - **macOS：** <br>
    `"$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/tools/ResourceExtractor/ResourceExtractor" "$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources" "$HOME/Documents/IsaacUnpacked"` <br>
    运行后，`.stb` 文件会被提取到 `$HOME/Documents/IsaacUnpacked/resources/rooms`。
- 接下来，就可以用 Basement Renovator 打开相应楼层的 STB 文件，查看其中的房间了。

### 如何添加或编辑房间

- 每个楼层的房间文件都有独立的文件名，且文件名以数字开头。对于可能出现在一局游戏不同楼层的特殊房间，请使用 `00.special rooms` 文件。
  - 从《忏悔》（Repentance）开始，也可以将特殊房间添加到指定楼层的文件中，使其仅在该楼层出现。

- 在 Rebirth 和 Afterbirth 中，可以直接覆盖保存 `[TBOI Install Folder]/resources/rooms` 下提取出的文件，以替换游戏加载的原版房间。

- 对于 Afterbirth+ 及后续版本，请将修改后的 STB 文件保存到你的模组（mod）目录，例如 `[TBOI Install Folder]/mods/[YourModName]` 或 `C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]`：
  - 如果保存到 `[YourModName]/resources/rooms/`，游戏加载时会使用你的文件覆盖相应楼层的原版房间数据。
    - **注意：** 这种方式会与其他采用相同方法替换楼层文件的模组**不兼容**，因此不推荐使用。
  - 如果保存到 `[YourModName]/content/rooms/`，你的房间会被添加到相应文件所对应的房间池中，而非直接替换原版房间。
    - **必须**使用与游戏原版资源目录中对应文件完全一致的文件名，否则房间无法正确加载。

### 如何使用编辑器界面

- 建议先按照上面的说明，用 Basement Renovator 打开一个原版楼层的 STB 文件，熟悉编辑器的操作。程序可以直接读取和保存 STB 文件，无须先转换为 XML。

- **编辑区（The Editor）：** 窗口中央是主要的房间编辑区。按住鼠标拖动实体即可移动它；也可以通过拖动选框，一次选中多个实体。选中的实体可以在房间内自由移动，也可以通过菜单或快捷键剪切、粘贴。要删除实体，先选中它，再按 **Backspace（退格键）** 或 **Delete（删除键）**。右键单击已有实体，即可将其替换为实体面板中当前选中的实体。双击房门可以切换其启用或禁用状态。

- **房间列表（The Room List）：** 窗口右侧是房间列表面板，可以拖动其标题栏改变位置。单击列表中的房间，即可在编辑区打开该房间。房间名称左侧的图标表示房间类型，名称旁边的数字是房间 ID。房间类型决定其道具池和场景贴图集（tileset）。点击 `add` 可以创建新房间；选中房间后按 **Backspace**、**Delete** 或点击 `delete` 可以删除房间；点击 `duplicate` 可以复制选中的房间（副本会使用不同的变体编号）。

- **房间列表（续）：** 双击房间可重命名；将鼠标悬停在房间上，可通过提示框查看有关信息；右键点击房间，可调整房间尺寸、类型、权重（影响其生成频率）和难度（用于控制楼层难度）。在列表中拖放房间可调整顺序，顶部的筛选器可用于只显示符合条件的房间。底部的 `Export`（导出）按钮可将所有选中的房间导出到新的 STB 文件；如果选择已有的 STB 文件，则会将这些房间追加到该文件中。

- **实体面板（The Entity Palette）：** 窗口左侧是实体面板，和房间列表一样可以移动。你可以像使用绘图软件一样，把实体“盖章”到编辑区：先在实体面板中选择一个实体，再在编辑区中希望放置它的位置点击鼠标右键。面板列出了已知的游戏实体。
  - 添加、移动或删除实体时，如果实体位于房门前方，房门会自动根据遮挡情况启用或禁用。若要手动覆盖自动判断的状态，可双击房门切换。
    - 如果不希望某个实体阻挡房门，可以为其添加 `NoBlockDoors` 属性。

- **其他操作：** 可以通过 `Edit`（编辑）菜单或快捷键 **Ctrl+G**（macOS 上为 **Cmd+G**）显示或隐藏网格。各个停靠面板都可以移动到窗口中的其他位置、设置为浮动窗口，或合并成选项卡。`View`（视图）菜单中还有其他显示选项。

- **测试菜单（Test Menu）：** 你可以直接通过 Basement Renovator 在游戏中测试房间，既可以一次测试一个房间，也可以选择多个房间。测试时，程序会将你传送到当前文件对应的楼层。具体测试方式如下：
  - **Replace Stage（替换楼层）：**
    - 使用选中的房间替换当前文件所对应楼层的房间。
    - 每次测试都会提供一些有用的道具和调试命令。
    - 如果房间是窄形或长形（即只有两个门位），会额外添加一个用于填充的 1×1 房间。
    - 此方式无法替换其他模组添加到该楼层的房间，因此那些房间可能干扰测试。
  - **Replace Starting Room（替换初始房间）：**
    - 将游戏的全局初始房间替换为当前选中的房间。
    - 不支持同时测试多个房间。
    - 不支持窄形、长形和标准 L 形房间（但支持储藏间）。
  - **InstaPreview（即时预览）：**
    - 跳过游戏菜单，启动游戏后直接进入选中房间中的第一个。
    - 选择了多个房间时，可以用 `,` 和 `.` 键切换。
    - 在房间内执行重置（Reset）操作时，玩家会沿顺时针方向移动到该房间的下一个门位。
      - 按 `;` 可切换是否留在当前门位。
      - 不适用于该房间的门位会显示为带红色禁止标记的门。
    - 每次只测试一个房间时，这种方式最接近原版游戏的行为。
  - 启用 `Disable In-Game UI`（禁用游戏内界面）设置后，可以隐藏游戏中的信息文字和带颜色的门。
    - 在游戏内也可以按 `u` 切换此设置。

### 常见问题（F.A.Q.）

*InstaPreview（即时预览）无法正常工作，怎么办？*

- 使用文本编辑器打开 Basement Renovator 所在目录中的 `settings.ini`，确认其中有一行 `InstallFolder=(...)`，并将 `(...)` 替换为包含游戏可执行文件的《以撒的结合》安装目录。

*如何为特定 DLC 或《抗生》（Antibirth）创建、编辑房间？*

- 使用文本编辑器打开 Basement Renovator 所在目录中的 `settings.ini`。添加以 `CompatibilityMode=` 开头的一行，后面填入以下版本名称之一：
    - `Rebirth`
    - `Afterbirth`
    - `Afterbirth+`
    - `Repentance`
    - `Repentance+`（默认）
    - `Antibirth`
- 这个设置会根据所选版本限制或调整编辑器中的可用内容。（如果发现内容与实际游戏不符，欢迎反馈或协助更新！）
  - 按照 [REPENTOGON 的配置说明](https://repentogon.com/install.html#how-do-i-use-basement-renovator-with-repentogon) 中的步骤进行配置，可以在《忏悔+》（Repentance+）兼容模式下启用一些额外功能。
- Rebirth 和 Antibirth 使用专门的 `stb` 文件格式；从 Afterbirth 开始，其他版本都使用相同的二进制格式。

*我发现了一个 Bug！*

- 请在 [GitHub 上提交 Issue](https://github.com/Tempus/Basement-Renovator/issues)。
- 如果需要尽快获得帮助，也可以尝试前往：
  - [The Binding of Isaac Discord 服务器](https://discord.gg/isaac)的 **#isaac-mod-dev** 频道；
  - [Modding of Isaac Discord 服务器](https://discord.com/invite/modding-of-isaac-962027940131008653)的 **#modding** 频道。

*下一个版本什么时候发布？*

- 项目没有固定的发布计划。如果想使用最新版本的 Basement Renovator，建议按照上面的说明直接从源码运行程序。资源文件通常会在游戏更新后不久同步更新，因此届时记得获取最新版本。

*为什么不能编辑房门的位置？为什么不能自定义房间尺寸？*

- 因为这样做会导致游戏崩溃，所以编辑器没有提供这些功能。

*如何添加自定义实体？*

- 此功能仅适用于 Afterbirth+ 及之后版本的模组。请在模组根目录下创建名为 `basementrenovator` 的文件夹（模组本身必须位于游戏的模组总目录内，才能被检测到）。然后在该文件夹中创建 `EntitiesMod.xml` 文件，其格式和约定应与 `resources/EntitiesAfterbirthPlus.xml` 相同。如果省略 `Group`，默认分组名称的格式为 `(Mod) Your Mod Name`（其中 `Your Mod Name` 代表你的模组名称）。`Image` 路径以模组内的 `basementrenovator` 文件夹为基准。为了减少不必要的内容并缩短启动时间，Basement Renovator 只会加载**已启用**的模组。
- 如果实体在游戏内的实际显示位置与所占网格位置有偏移，可以使用 `PlaceVisual` 属性。示例参见 `resources/EntitiesRebirth`。属性值可以是 `X,Y`（以网格格数为单位，支持正负偏移），也可以是预定义的动态行为，例如 `WallSnap`。
  - 如果使用该属性为图标添加其他视觉标记，或实体贴图本身不对称，可以通过 `DisableOffsetIndicator` 关闭偏移指示标记（仅在偏移量超过半格时才有必要使用）。
- 新放置的网格实体会位于同一位置的普通实体下方。要使自定义实体具有这一性质，请添加 `IsGrid` 属性。
- 如果由于某些原因，你的实体不存在于 `entities2.xml` 中，可以为该实体添加 `Metadata="1"`。**请谨慎使用！** 此设置会屏蔽一些有用的错误提示，并允许 Basement Renovator 加载通常无法加载的实体。这主要适用于房间生成前使用的辅助实体，例如与 [Stage API](https://github.com/Meowlala/BOIStageAPI15) 配合使用的实体。
- 如果手动配置太麻烦，或者你想快速使用某个尚未提供 Basement Renovator 配置的大型模组中的实体，可以启用 `Autogenerate mod content`（自动生成模组内容）。此功能会自动扫描模组的 `content/entities2.xml`，而不是读取 `basementrenovator` 文件夹。不过，它有以下缺点：
  - 每次启动时，程序都必须为模组中的每个实体生成图标，这会拖慢启动速度。更大的问题是图标的选取方式：程序会直接使用默认动画的第一个可用帧。很多实体的效果尚可，但像 Gaper（裂口尸）这样将头部作为叠加图层的实体，生成的图标就会远不如手动挑选的图标合适。
  - 实体会自动按照 `Kind` 分类；如果某些实体需要特殊分类，程序可能无法正确判断。
  - 除了弹幕、跟班等少数例外，模组添加的**所有**实体都会出现在 Basement Renovator 中，包括那些不适合放进房间编辑器的实体。
  - 自动生成与手动配置两种方式不能混用，因此会失去另一种方式的优点。基于以上原因，**不推荐**启用该设置；使用 `basementrenovator` 文件夹进行配置通常更清晰、可靠。

*如何添加自定义楼层？*

- 过程与添加自定义实体类似：在模组中创建 `basementrenovator` 文件夹，再添加 `StagesMod.xml`。文件格式与约定应和 `resources/StagesRebirth.xml` 相同。
- `BaseGamePath`：该楼层在原版游戏中对应的 STB 文件名，不包含扩展名（自定义楼层通常用不到）。如果未指定，程序会将该楼层视为来自模组。
- `BGPrefix`：背景图片相对于 `basementrenovator` 文件夹的路径前缀。填写时应省略文件名末尾的 `-.png`，以及 L 形房间背景使用的 `-Inner.png`。如果省略此属性，程序会使用第一个 `Stage` 和 `StageType` 均相同、且背景有效的楼层作为备用背景。
- `Pattern`：用来匹配文件名并确定其所属楼层的模式。如果文件名包含指定前缀，就会被归入该楼层。后加载的楼层在前缀匹配时具有更高优先级，因此模组楼层总是优先于原版楼层。
- `Stage` 和 `StageType`：对应游戏内的楼层枚举值。对于模组楼层，应指向它所替换的原版楼层。
- `StageHPNum`：可选参数，用来计算使用「楼层生命值」（Stage HP）机制的敌人的总生命值。如果未指定，则使用 `Stage` 的值。
- `Name`：在 Basement Renovator 中显示的楼层名称；进行房间测试时也会传递该名称，以便在需要时正确替换原版楼层。

*如何让某些房间显示不同的背景，或添加新的房间类型？*

- 某些模组（例如 Revelations）添加了特殊的房间类型，如 Chill 房间。为这些房间设置不同的视觉效果，有助于将它们与该楼层的普通房间区分开来。
- 在模组内创建 `basementrenovator` 文件夹，再添加 `RoomTypesMod.xml`。其格式与约定应和 `resources/RoomTypesAfterbirthPlus.xml` 相同。
- 实体也可以包含一个 `Gfx` 子元素，格式与房间类型文件中的 `Gfx` 相同。当此实体出现在房间内时，房间背景会替换为它指定的 `Gfx`。
  - 如果房间中有多个这样的实体，则以坐标 `x + y` 之和最大的实体为准。
- 房间类型还可以指定额外的 `Subtype`，供创建或搜索房间时使用。要确保该房间类型显示在编辑器界面中，请在定义中添加 `Icon` 路径。建议使用 16×16 像素的房间图标，以避免显示模糊。

*有没有快速建立 Basement Renovator 兼容配置的方法？*

- 启用 `Autogenerate mod content` 后启动程序，可以快速生成一份可放入模组 `basementrenovator` 文件夹的初始配置。在 Basement Renovator 资源目录的 `Entities/ModTemp` 下，会出现一个以你的模组命名的文件夹，其中包含图标目录和 `EntitiesMod.xml` 文件。但自动生成的内容可能有很多你不需要的实体条目，因此仍须手动清理。
- 部分自动生成的图标可能不理想。例如，Gaper 的头部是叠加图层，生成的图标可能缺少头部；其他实体的第一帧也未必能代表其外观。Basement Renovator 在 `resources` 目录中提供了 `Icon Generator` 脚本，可以从 `.anm2` 动画的任意帧生成更合适的图标。运行脚本时添加 `--help` 或 `-h` 参数，可查看详细用法。
- 此方法不会生成自定义楼层的配置，因为程序无法确定模组是如何生成这些楼层的；这部分仍需手动设置。

*为什么我的自定义实体上出现了黄色警告标志？*

- Basement Renovator 虽然可以保存多种用于标识实体的数值，但不是所有数值都能在游戏中正确工作。有些数值即使在游戏中看似可用，仍属于无效范围。
  - **变体（Variant）：** 游戏中使用 12 位数值，范围为 **0–4095**。Basement Renovator 则以 32 位数值保存变体；游戏虽然能够读取这些数据，但实际使用的变体值会被缩减到 0–4095 的范围内。因此，只有原本就处于该范围内的变体值才能确保不发生变化。
  - **实体类型／ID（Type／ID）：** 与变体采用相同的数值表示方式，但还存在一个特殊情况：当实体类型达到 **1000 或更高**时，游戏会把它视为岩石、尖刺等**网格实体**。因此，如果自定义实体的类型 ID 处于这个范围，它就不会作为普通实体生成在房间中。
  - **子类型（Subtype）：** 在游戏和 Basement Renovator 中都使用 8 位数值，范围为 **0–255**；除此之外，其限制规则与变体相同。

  如果看到黄色警告，请将相应的数值调整到有效范围，以免模组出现难以排查的问题。具体是哪个值超出范围，可以查看日志，或将鼠标悬停在房间中的实体上查看提示框。

*那红色警告标志是什么意思？*

- 这表示 Basement Renovator 从自身的某个 XML 文件中读取了该实体，但未能在 `entities2.xml` 文件中找到对应的实体。也就是说，Basement Renovator 的 XML 中记录的实体类型、变体或子类型无效。**这是一个严重问题：游戏加载包含这种实体的房间时会崩溃！** 红色警告会优先于黄色警告显示，但同一实体也可能同时存在黄色警告所代表的数值范围问题。详情可查看实体的提示框。

*什么是 Hook（钩子）？*

- Basement Renovator 的某些工作流程要求用户反复手动处理导出的文件。例如，Afterbirth+ 的模组框架 [Stage API](https://github.com/Meowlala/BOIStageAPI15) 需要先将 STB 文件转换为 Lua 文件，才能正确使用这些房间。
- 为减少繁琐操作和人为错误，Basement Renovator 允许配置一组脚本，在处理相关文件的特定阶段自动执行。
  - **保存钩子（Save Hook）：** 保存房间文件时，程序会运行为该保存钩子配置的所有脚本，并将生成的 STB 文件路径作为参数传入，调用形式如下：`script.exe "path to file" --save`。额外的 `--save` 参数可以让同一脚本区分保存操作与其他用途。
    - Stage API 可利用该功能，在每次保存时自动将 STB 文件转换为 Lua 文件。
  - **测试钩子（Test Hook）：** 测试房间时，程序会先将房间输出为 XML 文件，然后将该文件传给脚本，例如：`script.exe "path to file" --test`。
    - Stage API 可利用该功能，在测试房间时生成所需的测试房间文件。
- 可以通过 `File > Set Hooks` 菜单配置钩子。