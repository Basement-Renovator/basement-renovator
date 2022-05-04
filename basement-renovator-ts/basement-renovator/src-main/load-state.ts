import { LookupProvider } from "../src/lookup";

export default async function LoadState() {
    const version = 'Repentance';
    await LookupProvider.init(version);

    console.log('Stages', LookupProvider.Main.stages.lookup());
    console.log('RoomTypes', LookupProvider.Main.roomTypes.lookup());
    console.log('RoomShapes', LookupProvider.Main.roomShapes.lookup());
    console.log('Entities', LookupProvider.Main.entities.lookup());
};