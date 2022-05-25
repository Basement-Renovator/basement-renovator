import { contextBridge } from "electron";
import { LookupProvider } from "../common/lookup";

const loadP = (async () => {
    const version = 'Repentance';
    await LookupProvider.init(version);

    console.log('Stages', LookupProvider.Main.stages.lookup());
    console.log('RoomTypes', LookupProvider.Main.roomTypes.lookup());
    console.log('RoomShapes', LookupProvider.Main.roomShapes.lookup());
    console.log('Entities', LookupProvider.Main.entities.entityListByType);
    console.log('Formats', LookupProvider.Main.formats.formats);
})();
export default loadP;

contextBridge.exposeInMainWorld('resourceLoadP', async (): Promise<void> => { await loadP; });
contextBridge.exposeInMainWorld('resources', () => LookupProvider.Main);