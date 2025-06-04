import { graphView } from "@web/views/graph/graph_view";
import { registry } from "@web/core/registry";

import { LinkTrackerGraphModel } from "./link_tracker_graph_model";

export const LinkTrackerGraphView = {
    ...graphView,
    Model: LinkTrackerGraphModel,
};

registry.category("views").add("link_tracker_graph_view", LinkTrackerGraphView);
