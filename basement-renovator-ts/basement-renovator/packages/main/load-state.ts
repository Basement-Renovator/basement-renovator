import { contextBridge } from "electron";
import { LookupProvider } from "../common/lookup";

const loadP = (async () => {
    const version = 'Repentance';
    await LookupProvider.init(version);

    //console.log('Stages', LookupProvider.Main.stages.lookup());
    //console.log('RoomTypes', LookupProvider.Main.roomTypes.lookup());
    //console.log('RoomShapes', LookupProvider.Main.roomShapes.lookup());
    //console.log('Entities', LookupProvider.Main.entities.entityListByType);
    //console.log('Formats', LookupProvider.Main.formats.formats);

    // wait for all imagemanagers from all mods so all paths are cleaned up
    console.log('Waiting for images');
    await Promise.all(LookupProvider.Main.mods.map(mod => mod.imageManager.waitAll()));
    console.log('Done');
})();
export default loadP;

