
BasementRenovator = BasementRenovator or { subscribers = {} }
BasementRenovator.mod = RegisterMod('BasementRenovator', 1)

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

if not BasementRenovator.TestRoomData then
    log('No room to test; please disable the mod')
    return
else
    local room = BasementRenovator.TestRoomData
    log('TEST METHOD: ' .. BasementRenovator.TestRoomData.TestType)
    log('TEST STAGE: ' .. room.Stage .. '.' .. room.StageType)
    log('TEST ROOM: ' .. room.Type .. '.' .. room.Variant .. '.' .. room.Subtype)
    log('TEST FILE: ' .. room.RoomFile)
end

function BasementRenovator:IsTestRoom(data)
    local test = BasementRenovator.TestRoomData

    local t, v, s, sh = test.Type, test.Variant, test.Subtype, test.Shape
    return data.Type == t and data.Variant == v and data.Subtype == s and data.Shape == sh
end

function BasementRenovator:InTestRoom()
    local level = Game():GetLevel()
    local desc = level:GetCurrentRoomDesc()
    if BasementRenovator:IsTestRoom(desc.Data) then
        return desc
    end
end

function BasementRenovator:InTestStage(level)
    level = level or Game():GetLevel()
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

local maxFloorRetries = 150
local floorRetries = 0
local loadingFloor = false
BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, function()
    local test = BasementRenovator.TestRoomData
    floorRetries = 0

    if test.TestType == 'StageReplace' then
        local player = Game():GetPlayer(0)
        player:AddCollectible(CollectibleType.COLLECTIBLE_MIND, 0, false)
        player:AddCollectible(CollectibleType.COLLECTIBLE_DADS_KEY, 0, false)
        Isaac.ExecuteCommand('debug 8')
        Game():GetSeeds():AddSeedEffect(SeedEffect.SEED_PREVENT_CURSE_LOST)
        loadingFloor = true
    end
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
    local game = Game()
    local level = game:GetLevel()
    if not loadingFloor or test.TestType ~= 'StageReplace' or not BasementRenovator:InTestStage(level) then
        return
    end

    local roomsList = level:GetRooms()
    local hasRoom
    for i = 0, roomsList.Size do
        local roomDesc = roomsList:Get(i)

        hasRoom = roomDesc and BasementRenovator:IsTestRoom(roomDesc.Data)
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
    local desc = BasementRenovator:InTestRoom()
    if desc then
        fireCallback('TestRoom', BasementRenovator.TestRoomData, desc)
    end
end)

BasementRenovator.mod:AddCallback(ModCallbacks.MC_PRE_ROOM_ENTITY_SPAWN, function(_, ...)
    local desc = BasementRenovator:InTestRoom()
    if desc then
        local replacement = fireCallback('TestRoomEntitySpawn', BasementRenovator.TestRoomData, desc, ...)
        if replacement then
            return replacement
        end
    end
end)

BasementRenovator.mod:AddCallback(ModCallbacks.MC_POST_RENDER, function()
    local test = BasementRenovator.TestRoomData
    local desc = BasementRenovator:InTestRoom()

    parts = split(test.RoomFile, '/\\')
    filename = parts[#parts]

    local pos = Game():GetRoom():GetRenderSurfaceTopLeft() * 2 + Vector(-20,286) --Vector(442,286)
    Isaac.RenderScaledText("BASEMENT RENOVATOR TEST: " .. test.Name .. " (" .. test.Variant .. ") [" .. filename .. ']', pos.X, pos.Y - 28, 0.5, 0.5, 255, 255, 0, 0.75)
    Isaac.RenderScaledText("Test Type: " .. test.TestType .. " --- In Test Room: " .. (desc and 'YES' or 'NO'), pos.X, pos.Y - 20, 0.5, 0.5, 255, 255, 0, 0.75)
end)