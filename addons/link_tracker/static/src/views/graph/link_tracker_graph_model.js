import { GraphModel } from "@web/views/graph/graph_model";

export class LinkTrackerGraphModel extends GraphModel {
    /**
     * @override
     * Remove the default __count measure
     */
    _buildMetaData(params) {
        const metaData = super._buildMetaData(params);
        if (Object.keys(metaData.measures).length > 1) {
            delete metaData.measures.__count;
        }
        return metaData;
    }
}
