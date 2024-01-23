
BasementRenovator = BasementRenovator or { subscribers = {} }
BasementRenovator.mod = RegisterMod('BasementRenovator', 1)

local game = Game()
local veczero = Vector(0,0)

setmetatable(BasementRenovator.subscribers, {
    __newindex = function(t, k, v)
        if v.PostTestInit and BasementRenovator.Loaded then
            v.PostTestInit(BasementRenovator.TestRoomData)
        end
        rawset(t, k, v)
    end
})

local function log(msg)
    msg = '[BasementRenovator] ' .. tostring(msg)
    print(msg)
    Isaac.DebugString(msg)
end

local function split(str, sep)
    local t = {}
    for s in string.gmatch(str, '([^'..sep..']+)') do
        table.insert(t, s)
    end
    if #t == 0 then table.insert(t, str) end

    return t
end

local function fireCallback(name, ...)
    for _, sub in pairs(BasementRenovator.subscribers) do
        local callback = sub[name]
        if callback then
            local result = callback(...)
            if result ~= nil then return result end
        end
    end
end

local success, data = pcall(require, 'roomTest')
if success then
    BasementRenovator.TestRoomData = data
else
    log(data) -- error
end

local RoomIndex = {}

if not BasementRenovator.TestRoomData then
    log('No room to test; please disable the mod')
    return
else
    local roomData = BasementRenovator.TestRoomData
    log('TEST METHOD: ' .. roomData.TestType)
    log('TEST STAGE: ' .. roomData.StageName .. ' (' .. roomData.Stage .. '.' .. roomData.StageType .. ')' .. (roomData.IsModStage and ' MOD' or ''))
    log('TEST FILE: ' .. roomData.RoomFile)
    log('TEST ROOMS:')
    for i, room in pairs(roomData.Rooms) do
        log(room.Type .. '.' .. room.Variant .. '.' .. room.Subtype)

        if not RoomIndex[room.Type] then RoomIndex[room.Type] = {} end
        local typeIndex = RoomIndex[room.Type]
        typeIndex[room.Variant] = room

        room.Index = i
    end
    roomData.CurrentIndex = 0
end

function BasementRenovator:GetTestRoomFromData(data)
    local test = BasementRenovator.TestRoomData

    local t, v, s, sh = data.Type, data.Variant, data.Subtype, data.Shape

    local room = RoomIndex[t]
    if not room then return nil end
    room = room[v]
    if not room then return nil end

    if room.Type == t and room.Variant == v and room.Subtype == s and room.Shape == sh then
        return room
    end
end

function BasementRenovator:InTestRoom()
    local level = game:GetLevel()
    local desc = level:GetCurrentRoomDesc()

    return BasementRenovator:GetTestRoomFromData(desc.Data), desc
end

function BasementRenovator:InTestStage(level)
    level = level or game:GetLevel()
    local test = BasementRenovator.TestRoomData
    return level:GetStage() == test.Stage and level:GetStageType() == test.StageType
end

local typeToSuffix = {
    [StageType.STAGETYPE_ORIGINAL] = "",
    [StageType.STAGETYPE_WOTL] = "a",
    [StageType.STAGETYPE_AFTERBIRTH] = "b"
}
function BasementRenovator:GotoTestStage()
    local test = BasementRenovator.TestRoomData
    local stage, type = test.Stage, test.StageType
    local type = typeToSuffix[type] or ''

    Isaac.ExecuteCommand('stage ' .. stage .. type)
end

BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_CURSE_EVAL, function(_, curse)
    local test = BasementRenovator.TestRoomData

    if test.TestType == 'StageReplace' then
        log('Forcing XL due to StageReplace!')
        return curse | LevelCurse.CURSE_OF_LABYRINTH
    end
end)

local newGame = false
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, function()
    newGame = true
end)

local hDoorSlots = { DoorSlot.LEFT0, DoorSlot.RIGHT0 }
local vDoorSlots = { DoorSlot.UP0, DoorSlot.DOWN0 }
BasementRenovator.DoorSlotOrder = {
    [RoomShape.ROOMSHAPE_1x1] = { DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.RIGHT0, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_1x2] = { DoorSlot.LEFT1, DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.RIGHT0, DoorSlot.RIGHT1, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_2x1] = { DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.DOWN1, DoorSlot.DOWN0 },

    [RoomShape.ROOMSHAPE_2x2] = { DoorSlot.LEFT1, DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.RIGHT1, DoorSlot.DOWN1, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_LTL] = { DoorSlot.LEFT1, DoorSlot.UP0, DoorSlot.LEFT0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.RIGHT1, DoorSlot.DOWN1, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_LTR] = { DoorSlot.LEFT1, DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.RIGHT0, DoorSlot.UP1, DoorSlot.RIGHT1, DoorSlot.DOWN1, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_LBL] = { DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.RIGHT1, DoorSlot.DOWN1, DoorSlot.LEFT1, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_LBR] = { DoorSlot.LEFT1, DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.DOWN1, DoorSlot.RIGHT1, DoorSlot.DOWN0 },

    [RoomShape.ROOMSHAPE_IH]  = hDoorSlots,
    [RoomShape.ROOMSHAPE_IIH] = hDoorSlots,
    [RoomShape.ROOMSHAPE_IV]  = vDoorSlots,
    [RoomShape.ROOMSHAPE_IIV] = vDoorSlots,
}

BasementRenovator.CurrentSlotIndex = -1
BasementRenovator.LockDoorSlot = false

local GotoTable = {
    [RoomType.ROOM_NULL]         = 'd', -- null rooms crash the game if added to files
    [RoomType.ROOM_DEFAULT]      = 'd', -- note that grave rooms don't work properly
    [RoomType.ROOM_SHOP]         = 's.shop',
    [RoomType.ROOM_ERROR]        = 's.error',
    [RoomType.ROOM_TREASURE]     = 's.treasure',
    [RoomType.ROOM_BOSS]         = 's.boss',
    [RoomType.ROOM_MINIBOSS]     = 's.miniboss',
    [RoomType.ROOM_SECRET]       = 's.secret',
    [RoomType.ROOM_SUPERSECRET]  = 's.supersecret',
    [RoomType.ROOM_ARCADE]       = 's.arcade',
    [RoomType.ROOM_CURSE]        = 's.curse',
    [RoomType.ROOM_CHALLENGE]    = 's.challenge',
    [RoomType.ROOM_LIBRARY]      = 's.library',
    [RoomType.ROOM_SACRIFICE]    = 's.sacrifice',
    [RoomType.ROOM_DEVIL]        = 's.devil',
    [RoomType.ROOM_ANGEL]        = 's.angel',
    [RoomType.ROOM_DUNGEON]      = 's.itemdungeon',
    [RoomType.ROOM_BOSSRUSH]     = 's.bossrush',
    [RoomType.ROOM_ISAACS]       = 's.isaacs',
    [RoomType.ROOM_BARREN]       = 's.barren',
    [RoomType.ROOM_CHEST]        = 's.chest',
    [RoomType.ROOM_DICE]         = 's.dice',
    [RoomType.ROOM_BLACK_MARKET] = 's.blackmarket',
    [RoomType.ROOM_GREED_EXIT]   = 'd' -- greed entrance room doesn't have a goto category??? so they don't work either
}

local function GotoTestRoomIndex()
    local test = BasementRenovator.TestRoomData
    local newRoom = test.Rooms[test.CurrentIndex + 1]
    local gotoStr = 'goto ' .. GotoTable[newRoom.Type] .. '.' .. newRoom.Variant
    log(gotoStr)
    Isaac.ExecuteCommand(gotoStr)
end

local function pt(name, tainted)
  local char = Isaac.GetPlayerTypeByName(name, tainted)
  return char >= 0 and char or nil
end

local function tryGetPlayerType(name, tainted)
  if tainted == nil then
      local untainted = string.gsub(name, "^([Tt]ainted ?)", '')
      untainted = string.gsub(untainted, "([-_][bB])$", '')
      if untainted ~= name then
        return tryGetPlayerType(untainted, true)
      end
  end

  return pt(name, tainted)
      or pt(string.gsub(string.upper(name), ".*", "#%0_NAME"), tainted)
      or pt(string.gsub(name, "^(.)", string.upper), tainted)
end

local maxFloorRetries = 150
local floorRetries = 0
local loadingFloor = false
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    if not newGame then return end

    log('BEGIN RUN')

    local test = BasementRenovator.TestRoomData
    floorRetries = 0

    if test.Character then
        local player = Isaac.GetPlayer(0)
        local char = tryGetPlayerType(test.Character)
        if char then
            if player:GetPlayerType() ~= char and player.ChangePlayerType then
                log('CHARACTER: ' .. test.Character)
                player:ChangePlayerType(char)
            end
        else
            log("Invalid character! " .. test.Character)
        end
    end

    if test.TestType == 'StageReplace' then
        local player = Isaac.GetPlayer(0)
        player:AddCollectible(CollectibleType.COLLECTIBLE_MIND, 0, false)
        player:AddCollectible(CollectibleType.COLLECTIBLE_DADS_KEY, 0, false)
        Isaac.ExecuteCommand('debug 8')
        game:GetSeeds():AddSeedEffect(SeedEffect.SEED_PREVENT_CURSE_LOST)
        loadingFloor = true
    elseif test.TestType == 'InstaPreview' then
        local player = Isaac.GetPlayer(0)
        player:AddCollectible(CollectibleType.COLLECTIBLE_D7, 0, false)
        Isaac.ExecuteCommand('debug 8')
    end

    if test.CurrentIndex ~= 0 then
        GotoTestRoomIndex()
    end

    for i, command in ipairs(test.Commands) do
        if command ~= "" then
            log('COMMAND: ' .. command)
            local parts = split(command, ' ')
            -- repeat doesn't work with ExecuteCommand, so a shim is required
            if i > 1 and parts[1] == 'repeat' then
                local lastCommand = test.Commands[i - 1]
                for i = 1, tonumber(parts[2]) do
                    Isaac.ExecuteCommand(lastCommand)
                end
            else
                Isaac.ExecuteCommand(command)
            end
        end
    end

    newGame = false
end)

BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_CURSE_EVAL, function()
    local test = BasementRenovator.TestRoomData
    -- For whatever reasons, callbacks execute when the stage command is run from the console,
    -- but don't when used from lua
    -- This may be patched in Rep, so fix this then so the callback doesn't happen twice
    -- Use CURSE_EVAL because otherwise it'll usually happen after other level detection code

    if test.TestType ~= 'InstaPreview' then
        if not BasementRenovator:InTestStage() then
            BasementRenovator:GotoTestStage()
        end
    end

    fireCallback('TestStage', BasementRenovator.TestRoomData)
end)

BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    local test = BasementRenovator.TestRoomData
    local level = game:GetLevel()
    if not loadingFloor or test.TestType ~= 'StageReplace' or not BasementRenovator:InTestStage(level) then
        return
    end

    local roomsList = level:GetRooms()
    local hasRoom
    for i = 0, roomsList.Size do
        local roomDesc = roomsList:Get(i)

        hasRoom = roomDesc and BasementRenovator:GetTestRoomFromData(roomDesc.Data)
        if hasRoom then break end
    end

    if hasRoom then
        floorRetries = 0
        loadingFloor = false
        log('Found floor with room!')
    else
        floorRetries = floorRetries + 1
        if floorRetries > maxFloorRetries then
            log('Exceeded max attempts to find floor with test rooms')
            floorRetries = 0
            loadingFloor = false
            return
        end
        game:GetSeeds():ForgetStageSeed(test.Stage)
        BasementRenovator:GotoTestStage()
    end
end)

local DoorToDirection = {
    [DoorSlot.DOWN0] = Direction.DOWN,
    [DoorSlot.DOWN1] = Direction.DOWN,
    [DoorSlot.LEFT0] = Direction.LEFT,
    [DoorSlot.LEFT1] = Direction.LEFT,
    [DoorSlot.RIGHT0] = Direction.RIGHT,
    [DoorSlot.RIGHT1] = Direction.RIGHT,
    [DoorSlot.UP0] = Direction.UP,
    [DoorSlot.UP1] = Direction.UP
}

local DoorOffsetsByDirection = {
    [Direction.DOWN] = Vector(0, -15),
    [Direction.UP] = Vector(0, 15),
    [Direction.LEFT] = Vector(15, 0),
    [Direction.RIGHT] = Vector(-15, 0)
}

local function DirectionToDegrees(dir)
    return dir * 90 - 90
end

local FakeDoorVariant = Isaac.GetEntityVariantByName("Fake Door [BR]")
function BasementRenovator.RenderDoorSlots(room, doorSlots, enterSlot)
    if not room then
        -- intended for external callers, e.g. stageapi
        if BasementRenovator.TestRoomData.TestType ~= 'InstaPreview' then
            return
        end

        room = game:GetRoom()
        doorSlots = BasementRenovator.DoorSlotOrder[room:GetRoomShape()]
        enterSlot = doorSlots[math.max(BasementRenovator.CurrentSlotIndex, 0) + 1]
    end

    -- render invalid door slots as effects
    if BasementRenovator.TestRoomData.DisableUI ~= 1 then
        for _, slot in pairs(doorSlots) do
            local doorDir = DoorToDirection[slot]

            local door = Isaac.Spawn(1000, FakeDoorVariant, 0, room:GetDoorSlotPosition(slot), veczero, nil)
            local sprite = door:GetSprite()
            sprite.Rotation = DirectionToDegrees(doorDir)
            sprite.Offset = DoorOffsetsByDirection[doorDir]

            if not room:IsDoorSlotAllowed(slot) then
                sprite:ReplaceSpritesheet(0, 'basementrenovator/grid/invaliddoor.png')
                sprite:ReplaceSpritesheet(1, 'basementrenovator/grid/invaliddoor.png')
                sprite:ReplaceSpritesheet(2, 'basementrenovator/grid/invaliddoor.png')
                sprite:ReplaceSpritesheet(3, 'basementrenovator/grid/invaliddoor.png')
                sprite:LoadGraphics()
                sprite:Play('Closed', true)
                door:AddEntityFlags(EntityFlag.FLAG_RENDER_WALL)
            elseif slot == enterSlot then
                sprite:ReplaceSpritesheet(3, 'basementrenovator/grid/entrydoor.png')
                sprite:LoadGraphics()
            end
        end
    end
end

BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    local test = BasementRenovator.TestRoomData
    local testRoom = BasementRenovator:InTestRoom()
    if testRoom then
        if test.TestType == 'InstaPreview' then
            local room = game:GetRoom()
            local player = Isaac.GetPlayer(0)

            local playerPos
            if room:GetType() ~= RoomType.ROOM_DUNGEON then
                local doorSlots = BasementRenovator.DoorSlotOrder[room:GetRoomShape()]

                -- move the player's position to the next available door slot
                if not BasementRenovator.LockDoorSlot then
                    BasementRenovator.CurrentSlotIndex = (BasementRenovator.CurrentSlotIndex + 1) % #doorSlots
                    for i = 0, #doorSlots - 1 do
                        local slotIndex = (BasementRenovator.CurrentSlotIndex + i) % #doorSlots
                        local currentSlot = doorSlots[slotIndex + 1]
                        if room:IsDoorSlotAllowed(currentSlot) then
                            BasementRenovator.CurrentSlotIndex = slotIndex
                            break
                        end
                    end
                end

                local enterSlot = doorSlots[math.max(BasementRenovator.CurrentSlotIndex, 0) + 1]
                local doorPos = room:GetDoorSlotPosition(enterSlot)

                BasementRenovator.RenderDoorSlots(room, doorSlots, enterSlot)

                -- TODO for rep? change entry door to sync with our choice
                --room:RemoveGridEntity(room:GetGridIndex(doorPos), 0, false)

                -- makes transitions smoother kinda?
                local level = game:GetLevel()
                --room:RemoveDoor(level.EnterDoor)
                level.EnterDoor = enterSlot

                playerPos = room:GetClampedPosition(doorPos, player.Size * 2)
            else
                -- special logic for crawlspace doors
                -- only use black market entrance when wall is open
                doorSlots = {
                    -- the main entrance is always in grid 2; in TL L rooms you're snapped right above the wall
                    { EnterPos = room:GetGridPosition(2) },
                    -- it's always this position regardless of room shape
                    { EnterPos = Vector(480, 280), DoorCheck = function()
                        local coords = room:GetGridPosition(14)
                        for i = 0, room:GetGridHeight() - 1 do
                            if room:GetGridCollisionAtPos(coords) == GridCollisionClass.COLLISION_NONE then
                                return true
                            end
                            coords.Y = coords.Y + 40
                        end
                        return false
                    end }
                }

                -- move the player's position to the next available door slot
                if not BasementRenovator.LockDoorSlot then
                    BasementRenovator.CurrentSlotIndex = (BasementRenovator.CurrentSlotIndex + 1) % #doorSlots
                    for i = 0, #doorSlots - 1 do
                        local slotIndex = (BasementRenovator.CurrentSlotIndex + i) % #doorSlots
                        local currentSlot = doorSlots[slotIndex + 1]
                        if not currentSlot.DoorCheck or currentSlot.DoorCheck() then
                            BasementRenovator.CurrentSlotIndex = slotIndex
                            break
                        end
                    end
                end

                local enterSlot = doorSlots[math.max(BasementRenovator.CurrentSlotIndex, 0) + 1]
                local doorPos = enterSlot.EnterPos

                playerPos = doorPos
            end

            player.Position = playerPos
        end

        fireCallback('TestRoom', BasementRenovator.TestRoomData, testRoom)
    end
end)

BasementRenovator.mod:AddCallback(ModCallbacks.MC_PRE_ROOM_ENTITY_SPAWN, function(_, ...)
    local room = BasementRenovator:InTestRoom()
    if room then
        local replacement = fireCallback('TestRoomEntitySpawn', BasementRenovator.TestRoomData, room, ...)
        if replacement then
            return replacement
        end
    end
end)

local function SafeKeyboardTriggered(key, controllerIndex)
    return Input.IsButtonTriggered(key, controllerIndex) and not Input.IsButtonTriggered(key % 32, controllerIndex)
end

local LastRoomChangeFrame = -1
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    local test = BasementRenovator.TestRoomData
    local room, roomDesc = BasementRenovator:InTestRoom()

    room = room or { Name = 'N/A', Variant = -1, Difficulty = -1, Invalid = true }

    local parts = split(test.RoomFile, '/\\')
    local filename = parts[#parts]

    if filename == '.' then
        filename = 'New File'
    end

    local topLeft = game:GetRoom():GetRenderSurfaceTopLeft()
    local pos = Vector(20, topLeft.Y * 2 + 286) --Vector(442,286)
    if BasementRenovator.TestRoomData.DisableUI ~= 1 then
        Isaac.RenderScaledText("BASEMENT RENOVATOR TEST: " .. room.Name .. " (" .. room.Variant .. ", Difficulty: " .. roomDesc.Data.Difficulty .. ") [" .. filename .. ']', pos.X, pos.Y - 28, 0.5, 0.5, 255, 255, 0, 0.75)
        Isaac.RenderScaledText("Test Type: " .. test.TestType ..  " --- In Test Room: " .. (room.Invalid and 'NO' or ('YES' .. (BasementRenovator.LockDoorSlot and ' [DOOR SLOT LOCKED]' or ''))), pos.X, pos.Y - 20, 0.5, 0.5, 255, 255, 0, 0.75)
    end

    local enableCycling = false
    if #test.Rooms > 1 and test.TestType == 'InstaPreview' then
        enableCycling = true
        if BasementRenovator.TestRoomData.DisableUI ~= 1 then
            Isaac.RenderScaledText("Press . (period) to cycle forward and , (comma) to go back. Current: " .. (test.CurrentIndex + 1) .. '/' .. #test.Rooms, pos.X, pos.Y - 36, 0.5, 0.5, 0, 255, 255, 0.75)
        end
    end

    local frame = game:GetFrameCount()
    if not game:IsPaused() and LastRoomChangeFrame ~= frame then
        local player = Isaac.GetPlayer(0)
        local ci = player.ControllerIndex

        if SafeKeyboardTriggered(Keyboard.KEY_R, ci) then
            -- fast reset
            Isaac.ExecuteCommand('restart')
        end

        if SafeKeyboardTriggered(Keyboard.KEY_SEMICOLON, ci) then
            -- toggle lock door slot
            BasementRenovator.LockDoorSlot = not BasementRenovator.LockDoorSlot
        end

        if enableCycling then
            local oldIndex = test.CurrentIndex

            if SafeKeyboardTriggered(Keyboard.KEY_COMMA, ci) then
                -- go back one room
                test.CurrentIndex = test.CurrentIndex - 1
            elseif SafeKeyboardTriggered(Keyboard.KEY_PERIOD, ci) then
                -- go forward one room
                test.CurrentIndex = test.CurrentIndex + 1
            end
            test.CurrentIndex = (test.CurrentIndex + #test.Rooms) % #test.Rooms

            if oldIndex ~= test.CurrentIndex then
                BasementRenovator.CurrentSlotIndex = -1
                BasementRenovator.LockDoorSlot = false
                GotoTestRoomIndex()
            end
        end
    end
end)

fireCallback('PostTestInit', BasementRenovator.TestRoomData)
BasementRenovator.Loaded = true