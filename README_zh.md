<span>[ <a href="README.md">English</a> | 中文 ]</span>
# 地下室编辑器

- “地下室编辑器”是游戏[《以撒的结合：重生》](https://store.steampowered.com/app/1426300/The_Binding_of_Isaac_Repentance/)的第三方房间/关卡编辑器.
- 它让编辑房间更加简单，甚至被官方人员使用。
- 它是开源的，使用[Python 3](https://www.python.org/)编写.
- 它最初由[Chronometrics](http://www.chronometry.ca/)编写，现在由[budjmt](https://github.com/budjmt)提供支持.
- 它也可以用来编辑[Afterbirth+](https://store.steampowered.com/app/570660/The_Binding_of_Isaac_Afterbirth/)、[Afterbirth](https://store.steampowered.com/app/401920/The_Binding_of_Isaac_Afterbirth/)和[Rebirth](https://store.steampowered.com/app/250900/The_Binding_of_Isaac_Rebirth/)版本的房间，但是一些实体ID可能会不正确。

### 下载

最新的地下室编辑器可以在[releases section](https://github.com/Basement-Renovator/Basement-Renovator/releases)获取，不过如果你想的话也可以运行源代码。

### 从源码运行

* 见 [INSTALL.md](INSTALL.md#running-from-source).

### 如何创建一个修改原版游戏房间的mod

- 如果你想编辑Rebirth或Afterbirth版本，你必须使用[Rick's Unpacker](http://svn.gib.me/builds/rebirth/) 来获取STB文件。如果你想编辑最新版本的游戏（Afterbirth+或Repentance），看下面的内容。
- 首先，使用官方的解包工具解包游戏的资源。
  - 在Windows上：<br>
  `C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\tools\ResourceExtractor\ResourceExtractor.exe` <br>
  （这会把`C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\rooms`文件夹填满.stb文件）（Repentance+的路径是`C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\extracted_resources\resources\rooms`）
  - 在MacOS上: <br>
  `"$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/tools/ResourceExtractor/ResourceExtractor" "$HOME/Library/Application Support/Steam/SteamApps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources" "$HOME/Documents/IsaacUnpacked"` <br>
  （这会把`$HOME/Documents/IsaacUnpacked/resources/rooms`文件夹填满.stb文件）
- 现在，你可以打开地下室编辑器，并用它打开一个楼层的STB文件，随意编辑它。
- 当你保存你的文件后，把修改后的STB文件放到你的mod的资源文件夹里（例如`C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]\resources`），它会把原版游戏的楼层版本替换掉。注意你的mod将会和其他相同方法修改的mod**不兼容**，所以这种方法不是很推荐。

### 如何创建一个包含额外房间的mod

- 使用地下室编辑器创建一个新的STB文件，只包含你想添加的额外房间。然后，重命名使它和原版楼层STB文件的文件名完全一样（读一下上面的“如何创建一个修改原版游房间的mod”部分，这样你就可以知道原版楼层的STB文件名是什么）。
- 当你保存你的文件后，把修改后的STB文件放到你的mod的资源文件夹里（例如`C:\Users\[YourUsername]\Documents\My Games\Binding of Isaac Afterbirth+ Mods\[YourModName]\content\rooms`），这样它就会添加额外的房间到游戏里。

### 如何使用编辑器界面

- 你应该首先打开一个原版游戏的STB楼层文件，去看看这个编辑器是如何工作的。跟随“如何创建一个修改原版游房间的mod”部分的步骤以获取文件。地下室编辑器可以直接读取和保存这些文件，不需要转换成XML。

- **The Editor（编辑器）**：在最中央的是主编辑器。你可以通过点击来选中一个目标或者拖动一个框来选中多个目标，然后可以随意拖动它们；你可以用菜单栏或者快捷键来剪切或者粘贴实体，也可以用回车或者删除键来删除实体；按住Alt键并单击实体，可以使用剪切板里的实体来替换它；你可以通过双击门来让它们启用或停用。

- **The Room List（房间列表）**: 在右侧是房间列表，这个窗口可以通过抓住上面的标题栏来移动。点击任何房间从而加载到主编辑器中。房间的种类使用房间项目左侧的图标标记出来了，ID是名字以外的数字。房间的种类决定了道具池和地砖样式。点击“add”选项以新建房间，按回车/删除键或者“delete”选项可以删除选中的房间，点击“duplicate”选项以复制房间（复制会有不一样的变体数字）。

- **The Room List（续）**：双击一个房间来改变它的名字，鼠标悬停在房间上可以看到一些信息，右键房间可以修改房间大小、类型、权重（它生成的频率）和难度（用于控制整个楼层的生成），拖动房间可以修改它们的顺序。在最顶上的过滤器可以筛选房间（你可能需要悬停鼠标以查看按钮的功能）。导出按钮可以导出所有选中的房间到一个新的STB文件中，如果选择的是已存在的STB文件则将会将它们加入到原本的STB中。

- **The Entity Palette（实体调色板）**：在左侧是实体调色板，可以像房间列表一样拖动。你可以用它在主编辑器中新建实体，就像在Mario Paint里那样。选择一个实体，然后在你想要创建实体的地方右键即可，就像盖印章一样。所有已知的游戏实体都在列表中。
  - 当你在添加、移动或者删除实体时，门会自动根据实体是否在它们前方来启用或停用。如果想覆盖正常的设置，双击门来修改是否启用。
    - 如果不想一个实体会挡住门，给它`NoBlockDoors`属性。

- **其他事情**：你可以显示或者隐藏网格，或者按Cmd-G（win上是Ctrl-G）。你可以拖动任何窗口，移动到新的区域，让它们悬浮，或者堆叠成标签。视图菜单中还有一些其他选项供你选择。

- **Test Menu**：想要快速测试你的房间，你可以直接从地下室编辑器中加载它们。你可以选择多个房间一起测试，或者只选择一个。你会被传送到当前文件的正确楼层。下面是不同测试方法的总结：
  - Replace Stage（替换楼层）
    - 将当前的楼层替换为当前文件选中的房间
    - 添加有用的物品和调试命令
    - 如果房间是狭窄的或者长的（即只有两个门），一个1x1的填充房间会被添加
    - 注意这种方法不能替换掉由mod添加到楼层的房间，所以它们可能会干扰
  - Replace Starting Room（替换起始房间）
    - 将全局的起始房间替换为当前选中的房间
    - 不会由多个房间生效
    - 不会由狭窄的、长的和标准的L形房间生效（贮藏室是可以的）
  - InstaPreview（快速预览）
    - 打开游戏，直接进入选中的第一个房间，跳过所有菜单
    - 在多个房间之间按`,`和`.`键来切换
    - 按`R`重新开始当前房间，会让玩家移动到房间中下一个顺时针的门
        - 使用`;`键来切换是否留在当前门
        - 不合法的门会被标记为红色
    - 对于单个房间来说，大部分内容和原本的游戏一样
  - 在游戏中的信息文本和有颜色的门可以通过启用“Disable In-Game UI（禁用游戏内UI）”设置来隐藏
    - 在游戏里也可以按`u`来切换这个设置


### F.A.Q.

*'InstaPreview（快速预览）'工具没有用，我应该怎么办？*
- 在地下室编辑器的文件夹中打开`settings.ini`文件，确保有一行写着：`InstallFolder=(...)`，其中(...)是包含游戏可执行文件的TBOI安装文件夹的位置

*我要怎么编辑Repentance的房间？*

- 打开地下室编辑器文件夹中的`settings.ini`文件，用文本编辑器打开。添加一行：`CompatibilityMode=Repentance`。其他有效值有`Rebirth`、`Afterbirth`、`Afterbirth+`和`Antibirth`
- 房间文件的格式和AB和AB+是一样的。

*我找到了一个bug！*

- 请[在github上新建一个issue](https://github.com/Tempus/Basement-Renovator/issues).
- 如果你需要快速的帮助，很多modding社区的人都在[BoI Discord服务器](https://discord.gg/isaac)的**#modding**频道里。

*什么时候会有新版本？*

- 我们没有正式的发布计划。如果你想运行地下室编辑器，建议你按照上面的步骤直接从源码运行mod。资源会在游戏更新后很快更新，所以在那时获取最新版本！

*为什么我不能修改门的位置？为什么我不能自定义房间大小？*

- 这会让游戏崩溃，所以它们不会在编辑器中出现。

*我怎么添加自定义实体？*

- 只有Afterbirth+的mod能生效。在你的mod的根目录下创建一个名为`basementrenovator`的文件夹（它必须在你的整个mod文件夹中才能被检测到）。在这个文件夹里，创建一个`EntitiesMod.xml`文件。这个文件应该使用和`resources/EntitiesAfterbirthPlus.xml`相同的格式和约定。如果`Group`被省略，它会默认为`(Mod) 你的mod名字`。`Image`路径是相对于你的mod中的`basementrenovator`文件夹的。最后，为了减少噪音和启动时间，地下室编辑器只会加载*启用*的mod。
- 如果你的实体在游戏中有一些偏移，你可以使用`PlaceVisual`属性。在`resources/EntitiesAfterbirthPlus`中有一些例子。它可以是`X,Y`，表示在网格中的偏移，也可以是预先编码的动态行为，比如`WallSnap`。
  - 如果你正在使用这个属性来添加额外的视觉指示符到你的图标，或者sprite本身是不对称的，你可以使用`DisableOffsetIndicator`来禁用这个偏移的视觉指示符（只有在偏移大于半个网格时才需要）
- 当新生成时，网格实体会被放在它们所在堆栈的正常实体下面。要给实体这个性质，添加`IsGrid`属性。
- 如果你有一个实体在`entities2.xml`中不存在，你可以给你的实体添加`Metadata="1"`。确保你知道你在做什么！这会抑制有用的错误信息，并允许地下室编辑器加载它通常不会加载的实体。（这种情况主要是和[Stage API](https://github.com/Meowlala/BOIStageAPI15)一起使用的辅助实体有关）
- 如果你觉得上述方法太麻烦了，或者你想快速创建带有大型mod实体的房间，而这些mod没有相关支持，你可以打开*Autogenerate mod content*设置。这将获取mod的`content/entities2.xml`而不是`basementrenovator`文件夹，并且可以在没有任何额外工作的情况下自动工作。*然而*，这带来了一些缺点：
  - 在每次程序启动的时候，地下室编辑器都必须为每一个实体生成一次图片，这会让它稍微慢一点，但比这更糟糕的是图片的选择方式。由于缺乏更好的方法，默认动画的第一个可用帧将被使用。这对于许多实体来说都很好，但对于像裂口尸这样的实体，它们有一个默认的身体动画，而头部只是一个覆盖层，如此选出的图片与精心挑选的图片相比非常糟糕。
  - 实体的类型会被自动分类，所以如果你需要特别分类一些实体，这个方法就没法智能检测到它。
  - 每一个实体（除了一些像泪弹这样的例外）都会出现在地下室编辑器中——所有的，包括那些没有任何意义的实体。
  - 这些技术不能混合使用，所以你会失去另一个选项的优势。因此，不建议使用这个设置。使用`basementrenovator`文件夹会更方便。

*我怎么添加自定义楼层？*

- 这和添加自定义实体非常相似。创建一个`basementrenovator`文件夹，然后添加一个名为`StagesMod.xml`的文件。这个文件应该使用和`resources/StagesAfterbirthPlus.xml`相同的格式和约定。
- `BaseGamePath`是对于那个楼层的游戏STB文件名的无扩展版本（这很可能不适用于你的mod楼层）。如果没有，那么这个楼层会被认为是来自mod的。
- `BGPrefix`是相对于`basementrenovator`文件夹的背景文件的路径，减去-.png和-Inner.png用于L形房间。如果省略，备选项将是第一个具有相同Stage和StageType的有效背景的阶段。
- `Pattern`是用于匹配文件名的模式，以确定它是为哪个楼层；如果文件包含该前缀，它将被设置为该楼层。最后加载的楼层具有前缀匹配优先级，因此mod的楼层始终优先于基础游戏的楼层。
- `Stage`和`StageType`对应于游戏中的楼层枚举值，对于mod楼层，这应该指向被替换的楼层。
- `StageHPNum`是一个可选值，用于计算使用楼层血量的敌人的总血量。如果没有指定，那么将使用`Stage`。
- 最后，`Name`是在地下室编辑器中显示的名称，并且也传递给房间测试，以允许根据需要正确替换基础游戏楼层。

*我怎么获取一些房间来显示不同的背景？*

- 一些mod，比如Revelations，添加了专门的房间类型，比如Chill房间，它们有一些很有帮助的视觉指示符。
- 新建一个`basementrenovator`文件夹，添加一个名为`RoomTypesMod.xml`的文件。这个文件应该使用和`resources/RoomTypesAfterbirthPlus.xml`相同的格式和约定。
- 实体可以拥有一个子Gfx元素，遵循与RoomTypes文件相同的格式。当这个实体在一个房间中时，背景将被覆盖为那个Gfx。
  - 如果有多个在同一个房间中，那么x+y最大的那个会优先被使用。

*有没有方法能快速设置地下室编辑器的兼容性？*

- 你可以在启用了自动生成mod内容的情况下快速设置地下室编辑器的兼容性。在地下室编辑器的资源文件夹下的Entities/ModTemp中，会有一个以你的mod名字命名的文件夹。它会包含一个图标文件夹和一个EntitiesMod.xml文件。然而，这会为你可能不想要有条目的许多东西生成条目，所以你需要清理一下。
- 有些图标可能不是你想要的。例如，裂口尸会缺少他们的头部，因为它们的头部只是覆盖层；或者有些实体的第一帧可能不是一个好的代表。地下室编辑器包含一个Icon Generator脚本，可以在资源文件夹下生成更精细的图标。在命令行运行脚本时加上--help或-h选项来获取更多细节。
- 这个方法不会生成自定义楼层，因为不确定mod如何生成它们。你需要自己做这一步。

*为什么我的自定义实体上有一个黄色的危险标志？*

- 尽管地下室编辑器可以保存一系列用于识别实体的值，但并不是所有的值都能在游戏中正常工作。有些在游戏中没问题，有些是无效的。
  - 变体在游戏中表示为12位，范围是0-4095，但地下室编辑器将它们保存为32位值。游戏可以读取你的mod实体，但它总是会被缩减到这个范围。如果你的变体在这个范围内，你可以百分百确定你的变体没有问题。
  - ID/类型和变体有着相同的表示，但有一个额外的情况。类型为1000或更高的实体被读取为房间中的*网格实体*，比如岩石或尖刺。这意味着如果你的id很高，你的实体根本不会在房间中生成！
  - 子类型使用8位表示，范围是0-255。这在地下室编辑器和游戏中都是一样的。遵循与变体相同的规则。

  如果你看到了这个警告，请更改你的值以适应正确的范围。这将防止你的mod中出现很难调试的问题。你可以在日志中或者在房间中悬停在实体上时看到它的超出范围的提示。

*红色的又是怎么回事？*

- 这是因为地下室编辑器从它自己的XML文件中加载了这个实体，而没有在`entities2.xml`文件中找到匹配的实体。这意味着地下室编辑器XML文件中的类型、变体或子类型是无效的。这是一个非常危险的错误，因为加载一个没有匹配实体的房间会在加载房间时导致游戏崩溃！这将比黄色的危险标志更危险，但它可能也有这个问题。（查看实体的工具提示以获取更多信息）

*什么是hook（钩子）？*

- 一些工作机制在地下室编辑器中需要重复地获取一个输出文件并对其进行手动处理。最突出的例子是AB+ mod [Stage API](https://github.com/Meowlala/BOIStageAPI15)，它需要将STB文件转换为Lua文件，以便正确使用它们。
- 由于这个过程容易出错且繁琐，地下室编辑器允许用户设置一些脚本列表，这些脚本将在它们处理完相关文件之前的各个时间点执行。
  - 保存钩子：当一个房间文件被保存时，所有这些脚本都会被执行，参数是保存的STB文件。如果想要重用一个脚本文件，可以使用额外的--save参数。
    - 楼层API在每次保存楼层时都会使用这个功能将STB转换为Lua文件。
  - 测试钩子：当一个房间被测试时，它会被输出到一个XML文件。这个XML文件会被传递给一个脚本，就像这样：`script.exe "path to file" --test`。
    - 楼层API在测试楼层时使用这个功能来设置一个测试房间文件。
- 你可以在 File > Set Hooks 中设置钩子。
