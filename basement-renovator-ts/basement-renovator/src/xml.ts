import * as XML from 'fast-xml-parser';

type Attrib = {
    attrib: Record<string, number|string|boolean|unknown>;
};

type XmlParsedInner =
({ [tag: string]: XmlParsedInner; } & Partial<Attrib>)
| Attrib
| Array<XmlParsedInner>;

export type XmlParsed = {
    [tag: string]: XmlParsedInner;
};

export class Parser<T extends XmlParsed> {
    parser: XML.XMLParser;

    constructor(arrayTags: Array<string>) {
        const arrayTagsSet = new Set(arrayTags);
        this.parser = new XML.XMLParser({
            ignoreAttributes: false,
            attributesGroupName: 'attrib',
            parseAttributeValue: true,
            ignoreDeclaration: true,
            ignorePiTags: true,
            processEntities: false,
            textNodeName: 'innerText',
            isArray: (name, jpath) => arrayTagsSet.has(name) || arrayTagsSet.has(jpath),
            attributeValueProcessor: (name, val, jpath) => {
                switch (val) {
                case 'True':
                case 'true':
                case 'Yes':
                case 'yes':
                    return 'true';
                case 'False':
                case 'false':
                case 'No':
                case 'no':
                    return 'false';
                default:
                    return val;
                }
            },
        });
    }

    decode(xml: string | Buffer): T {
        return this.parser.parse(xml);
    }
}