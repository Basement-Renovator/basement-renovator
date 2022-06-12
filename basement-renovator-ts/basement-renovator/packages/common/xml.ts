import * as XML from 'fast-xml-parser';
import _ from 'lodash';

type Attrib = {
    attrib: Record<string, number|string|boolean|unknown>;
    innerText: string;
};

export type XmlParsed =
({ [tag: string]: XmlParsed; } & Partial<Attrib>)
| Partial<Attrib>
| Array<XmlParsed>;

export class Parser<T extends XmlParsed> {
    parser: XML.XMLParser;

    constructor(arrayTags: Array<string>, preserveOrder=false) {
        const arrayTagsSet = new Set(arrayTags);
        this.parser = new XML.XMLParser({
            ignoreAttributes: false,
            attributesGroupName: 'attrib',
            attributeNamePrefix: '',
            parseAttributeValue: true,
            ignoreDeclaration: true,
            ignorePiTags: true,
            processEntities: false,
            textNodeName: 'innerText',
            isArray: (name, jpath) => arrayTagsSet.has(name) || arrayTagsSet.has(jpath),
            preserveOrder,
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
        const obj = this.parser.parse(xml);

        function cleanUpTags(obj: Record<string, any>) {
            for (const [ key, val ] of Object.entries(obj)) {
                if (key === 'attrib') {
                    for (const [ k, v ] of Object.entries(val as Record<string, any>)) {
                        if (v === 'true') {
                            val[k] = true;
                        }
                        else if (v === 'false') {
                            val[k] = false;
                        }
                    }
                    continue;
                }

                if (key === ':@') {
                    Object.assign(obj, val);
                    delete obj[key];
                }

                // tags must start with lowercase
                if (key.match(/^[A-Z]/)) {
                    obj[_.lowerFirst(key)] = val;
                    delete obj[key];
                }

                if (Array.isArray(val)) {
                    val.forEach(cleanUpTags);
                }
                else if (typeof val === 'object') {
                    cleanUpTags(val);
                }
            }
        }

        cleanUpTags(obj);
        return obj;
    }
}