
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
        callback = sub[name]
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

    return BasementRenovator:GetTestRoomFromData(desc.Data)
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

local bigDoorSlots = { DoorSlot.LEFT1, DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.RIGHT1, DoorSlot.DOWN1, DoorSlot.DOWN0 }
local hDoorSlots = { DoorSlot.LEFT0, DoorSlot.RIGHT0 }
local vDoorSlots = { DoorSlot.UP0, DoorSlot.DOWN0 }
BasementRenovator.DoorSlotOrder = {
    [RoomShape.ROOMSHAPE_1x1] = { DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.RIGHT0, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_1x2] = { DoorSlot.LEFT1, DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.RIGHT0, DoorSlot.RIGHT1, DoorSlot.DOWN0 },
    [RoomShape.ROOMSHAPE_2x1] = { DoorSlot.LEFT0, DoorSlot.UP0, DoorSlot.UP1, DoorSlot.RIGHT0, DoorSlot.DOWN0, DoorSlot.DOWN1 },

    [RoomShape.ROOMSHAPE_2x2] = bigDoorSlots,
    [RoomShape.ROOMSHAPE_LTL] = bigDoorSlots,
    [RoomShape.ROOMSHAPE_LTR] = bigDoorSlots,
    [RoomShape.ROOMSHAPE_LBL] = bigDoorSlots,
    [RoomShape.ROOMSHAPE_LBR] = bigDoorSlots,

    [RoomShape.ROOMSHAPE_IH]  = hDoorSlots,
    [RoomShape.ROOMSHAPE_IIH] = hDoorSlots,
    [RoomShape.ROOMSHAPE_IV]  = vDoorSlots,
    [RoomShape.ROOMSHAPE_IIV] = vDoorSlots,
}

BasementRenovator.CurrentSlotIndex = -1
BasementRenovator.LockDoorSlot = false

local GotoTable = {
    [0] = 'd', -- null rooms crash the game if added to files
    [1] = 'd', -- note that grave rooms don't work properly
    [2] = 's.shop',
    [3] = 's.error',
    [4] = 's.treasure',
    [5] = 's.boss',
    [6] = 's.miniboss',
    [7] = 's.secret',
    [8] = 's.supersecret',
    [9] = 's.arcade',
    [10] = 's.curse',
    [11] = 's.challenge',
    [12] = 's.library',
    [13] = 's.sacrifice',
    [14] = 's.devil',
    [15] = 's.angel',
    [16] = 's.itemdungeon',
    [17] = 's.bossrush',
    [18] = 's.isaacs',
    [19] = 's.barren',
    [20] = 's.chest',
    [21] = 's.dice',
    [22] = 's.blackmarket',
    [23] = 'd' -- greed entrance room doesn't have a goto category??? so they don't work either
}

local function GotoTestRoomIndex()
    local test = BasementRenovator.TestRoomData
    local newRoom = test.Rooms[test.CurrentIndex + 1]
    local gotoStr = 'goto ' .. GotoTable[newRoom.Type] .. '.' .. newRoom.Variant
    log(gotoStr)
    Isaac.ExecuteCommand(gotoStr)
end

local maxFloorRetries = 150
local floorRetries = 0
local loadingFloor = false
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    if not newGame then return end

    log('BEGIN RUN')

    local test = BasementRenovator.TestRoomData
    floorRetries = 0

    -- omitted pending some update with instapreview, which is the main test mode that would benefit
    --[[if test.Character then
        local char = Isaac.GetPlayerTypeByName(test.Character)
        if char >= 0 then
            if Isaac.GetPlayer(0):GetPlayerType() ~= char then
                log('restart ' .. char)
                Isaac.ExecuteCommand('restart ' .. char)
                return
            end
        else
            log("Invalid character! " .. test.Character)
        end
    end]]

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

local IsFlippedDoor = {
    [DoorSlot.DOWN0] = true,
    [DoorSlot.DOWN1] = true,
    [DoorSlot.RIGHT0] = true,
    [DoorSlot.RIGHT1] = true,
}

local IsVertDoor = {
    [DoorSlot.UP0] = true,
    [DoorSlot.UP1] = true,
    [DoorSlot.DOWN0] = true,
    [DoorSlot.DOWN1] = true,
}

local FakeDoorVariant = Isaac.GetEntityVariantByName("Fake Door [BR]")
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    local test = BasementRenovator.TestRoomData
    local testRoom = BasementRenovator:InTestRoom()
    if testRoom then
        if test.TestType == 'InstaPreview' then
            local room = game:GetRoom()
            local doorSlots = BasementRenovator.DoorSlotOrder[room:GetRoomShape()]

            -- render invalid door slots as effects
            -- TODO does not work with xml L rooms properly due to vanilla bug
            for _, slot in pairs(doorSlots) do
                if not room:IsDoorSlotAllowed(slot) then
                    local isFlipped = IsFlippedDoor[slot]
                    local isVert = IsVertDoor[slot]
                    local door = Isaac.Spawn(1000, FakeDoorVariant, 0, room:GetDoorSlotPosition(slot), veczero, nil)
                    local sprite = door:GetSprite()
                    if not isVert then
                        sprite.Rotation = -90
                    end
                    sprite[isVert and 'FlipY' or 'FlipX'] = isFlipped

                    local offMult = isFlipped and -1 or 1
                    sprite.Offset = Vector((isVert and 0 or 15) * offMult, (isVert and 15 or 0)) -- bug? in FlipY, offset is flipped with sprite
                    REVEL.DebugLog(slot, sprite.Offset)
                end
            end

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

            local player = Isaac.GetPlayer(0)
            local slot = doorSlots[math.max(BasementRenovator.CurrentSlotIndex, 0) + 1]

            local playerPos = room:GetDoorSlotPosition(slot)
            playerPos = room:GetClampedPosition(playerPos, player.Size * 2)

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
    local room = BasementRenovator:InTestRoom() or { Name = 'N/A', Variant = -1, Invalid = true }

    parts = split(test.RoomFile, '/\\')
    filename = parts[#parts]

    local topLeft = game:GetRoom():GetRenderSurfaceTopLeft()
    local pos = Vector(20, topLeft.Y * 2 + 286) --Vector(442,286)
    Isaac.RenderScaledText("BASEMENT RENOVATOR TEST: " .. room.Name .. " (" .. room.Variant .. ") [" .. filename .. ']', pos.X, pos.Y - 28, 0.5, 0.5, 255, 255, 0, 0.75)
    Isaac.RenderScaledText("Test Type: " .. test.TestType ..  " --- In Test Room: " .. (room.Invalid and 'NO' or ('YES' .. (BasementRenovator.LockDoorSlot and ' [DOOR SLOT LOCKED]' or ''))), pos.X, pos.Y - 20, 0.5, 0.5, 255, 255, 0, 0.75)

    local enableCycling = false
    if #test.Rooms > 1 and test.TestType == 'InstaPreview' then
        enableCycling = true
        Isaac.RenderScaledText("Press . (period) to cycle forward and , (comma) to go back. Current: " .. (test.CurrentIndex + 1) .. '/' .. #test.Rooms, pos.X, pos.Y - 36, 0.5, 0.5, 0, 255, 255, 0.75)
    end

    local frame = game:GetFrameCount()
    if not game:IsPaused() and LastRoomChangeFrame ~= frame then
        local player = Isaac.GetPlayer(0)
        local ci = player.ControllerIndex

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