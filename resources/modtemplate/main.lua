
BasementRenovator = BasementRenovator or { subscribers = {} }
BasementRenovator.mod = RegisterMod('BasementRenovator', 1)

local game = Game()

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
    local test = BasementRenovator.TestRoomData

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

BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_NEW_ROOM, function()
    local room = BasementRenovator:InTestRoom()
    if room then
        fireCallback('TestRoom', BasementRenovator.TestRoomData, room)
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

local GotoTable = {
    [0] = 'd',
    [1] = 'd',
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
    [14] = 's.angel',
    [15] = 's.devil',
    [16] = 's.itemdungeon',
    [17] = 's.bossrush',
    [18] = 's.isaacs',
    [19] = 's.barren',
    [20] = 's.chest',
    [21] = 's.dice',
    [22] = 's.blackmarket',
    [23] = 'd' -- greed entrance room doesn't have a goto category???
}

local LastRoomChangeFrame = -1
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    local test = BasementRenovator.TestRoomData
    local room = BasementRenovator:InTestRoom() or { Name = 'N/A', Variant = -1, Invalid = true }

    parts = split(test.RoomFile, '/\\')
    filename = parts[#parts]

    local topLeft = game:GetRoom():GetRenderSurfaceTopLeft()
    local pos = Vector(20, topLeft.Y * 2 + 286) --Vector(442,286)
    Isaac.RenderScaledText("BASEMENT RENOVATOR TEST: " .. room.Name .. " (" .. room.Variant .. ") [" .. filename .. ']', pos.X, pos.Y - 28, 0.5, 0.5, 255, 255, 0, 0.75)
    Isaac.RenderScaledText("Test Type: " .. test.TestType .. " --- In Test Room: " .. (room.Invalid and 'NO' or 'YES'), pos.X, pos.Y - 20, 0.5, 0.5, 255, 255, 0, 0.75)

    local enableCycling = false
    if #test.Rooms > 1 and test.TestType == 'InstaPreview' then
        enableCycling = true
        Isaac.RenderScaledText("Press . (period) to cycle forward and , (comma) to go back. Current: " .. (test.CurrentIndex + 1) .. '/' .. #test.Rooms, pos.X, pos.Y - 36, 0.5, 0.5, 0, 255, 255, 0.75)
    end

    local frame = game:GetFrameCount()
    if enableCycling and not game:IsPaused() and LastRoomChangeFrame ~= frame then
        local oldIndex = test.CurrentIndex

        local player = Isaac.GetPlayer(0)
        local ci = player.ControllerIndex
        if SafeKeyboardTriggered(Keyboard.KEY_COMMA, ci) then
            -- go back one room
            test.CurrentIndex = test.CurrentIndex - 1
        elseif SafeKeyboardTriggered(Keyboard.KEY_PERIOD, ci) then
            -- go forward one room
            test.CurrentIndex = test.CurrentIndex + 1
        end
        test.CurrentIndex = (test.CurrentIndex + #test.Rooms) % #test.Rooms

        if oldIndex ~= test.CurrentIndex then
            local newRoom = test.Rooms[test.CurrentIndex + 1]
            Isaac.ExecuteCommand('goto ' .. GotoTable[newRoom.Type] .. '.' .. newRoom.Variant)
        end
    end
end)

fireCallback('PostTestInit', BasementRenovator.TestRoomData)
BasementRenovator.Loaded = true